""" Common stuff for handling music and MIDI """

from collections import OrderedDict
from pathlib import Path
from miditoolkit.midi import parser as mid_parser


CHROMATIC_SCALE = ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')
NOTE_NAME_MAP = {**{x: x for x in CHROMATIC_SCALE},
                 **{'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#', 'G#': 'Ab', 'A#': 'Bb'}}

MAJOR_INTERVALS = (2, 2, 1, 2, 2, 2, 1)
MAJOR_RANGE = (0, 2, 4, 5, 7, 9, 11)   # Offsets from tonic for major scale, wraps mod 8 and adds 12 at wrap
EWI_RANGE = (-2, -1) + MAJOR_RANGE + (10, 12, 14, 15)  # range of notes EWI can play w/o octave shift. Bb is easy

# solfa scale note names
# solfa = OrderedDict((('Do', '#c40233'),   # red
#                      ('di', '#fd4e7a'),   # pastel red
#                      ('Re', '#e16b1a'),   # orange
#                      ('ri', '#efa676'),   # pastel orange
#                      ('Mi', '#eac100'),   # yellow
#                      ('Fa', '#00a368'),   # green
#                      ('fi', '#00e691'),   # pastel green
#                      ('So', '#00e6e2'),   # aqua
#                      ('si', '#4dfffc'),   # pastel aqua
#                      ('La', '#0088bf'),   # blue
#                      ('li', '#80dbff'),   # pastel blue
#                      ('Ti', '#624579')))  # purple

solfa = OrderedDict((('Do', '#e31a1c'),   # red
                     ('di', '#fb9a99'),   # pastel red
                     ('Re', '#ff7f00'),   # orange
                     ('ri', '#fdbf6f'),   # pastel orange
                     ('Mi', '#F0E442'),   # yellow
                     ('Fa', '#4dac26'),   # green
                     ('fi', '#b5cf6b'),   # pastel green
                     ('So', '#5ab4ac'),   # aqua
                     ('si', '#c7eae5'),   # pastel aqua
                     ('La', '#6baed6'),   # blue
                     ('li', '#bfd3e6'),   # pastel blue
                     ('Ti', '#6a3d9a')))  # purple

solfa_list = list(solfa.items())

black_key = [(1 if x == x.lower() else 0) for x in solfa.keys()]

# color coded solfa mostly per https://en.wikipedia.org/wiki/File:Solresol_representations.svg
bg_colors = ['#f2f2f2',  # light gray diatonic note row background
             '#e6e6e6']  # gray chromatic accidentals row background

def midi_2_note(pitch: int):
    """
    Convert MIDI pitch to (note_name, octave)

    :param pitch: MIDI pitch
    :return: tuple(note_name, octave)
    """
    """Convert MIDI pitch to (note_name, octave)"""
    return (CHROMATIC_SCALE[(pitch - 24) % 12], int((pitch - 12)/12))


def note_2_midi(note_octave: str):
    """
    Convert a note-octave string to midi pitch

    :param note_octave: string for note-octave, e.g. C#-3
    :return:
    """
    name, octave = note_octave.capitalize().split('-')
    return CHROMATIC_SCALE.index(NOTE_NAME_MAP.get(name)) + 12 * (int(octave) + 1)

def midi_major(tonic_pitch: int):
    """
    MIDI pitches of major scale from tonic

    :param tonic_pitch: MIDI pitch for scale tonic
    :return: tuple(MIDI pitches of major scale)
    """
    return [midi_2_note(x) for x in [tonic_pitch + y for y in MAJOR_RANGE]]


def ewi_range(tonic_pitch: int):
    """
    MIDI pitches of diatonic notes and max/min notes playable on EWI w/o octave shift

    :param tonic_pitch:
    :return:
    """
    return set([tonic_pitch + y for y in EWI_RANGE])


def best_ewi_key(notes: {int}):
    """
    Find best key for EWI to play a song consisting of the set of pitches. Consider lowest note in song thru
    median note in song as tonic.

    :param notes: list of Note
    :return: MIDI pitch for tonic of key
    """

    pitches = [x.pitch for x in notes]
    pitchset = set(pitches)
    scores = {}
    for pitch in range(min(pitches), sorted(list(pitches))[len(pitches)//2]):
        ewi_scale = set(ewi_range(pitch))
        score = ((3.0 * len(ewi_scale & pitchset)
                 + len([n for n in pitchset if min(ewi_scale) <= n <= max(ewi_scale)])) / len(pitchset)
                 + 3.0 * len([x for x in pitches if x in ewi_scale]) / len(pitches))
        scores[score] = pitch
    return scores[max(scores.keys())]

def midi_to_solfa(midi_pitch, root_pitch):
    """
    Convert a MIDI pitch to solfa for a given scale root
    :param int midi_pitch: played note
    :param int root_pitch: root pitch
    :return: solfa note name
    """
    note = solfa_list[int((midi_pitch - root_pitch) % 12)][0]
    octave = round(((midi_pitch - root_pitch) - 5.9) / 12)
    return (f'{"<" * -octave} {note} {">" * octave}')


def get_notes(midi_file, track_name='MELODY'):
    """
    Get notes from MIDI file

    :param str midi: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :return: midi object, notes list
    """
    midi_path = Path(midi_file)
    midi_song = mid_parser.MidiFile(str(midi_path))
    track_index = None
    if len(midi_song.instruments) == 1:
        track_index = 0
    else:
        track_map = {str(name).strip().upper(): num for num, name in enumerate([t.name for t in midi_song.instruments])}
        track_index = track_map.get(str(track_name).strip().upper())
    if track_index is None:
        raise ValueError(f'No track {track_name} found in tracks {track_map}')
    notes = midi_song.instruments[track_index].notes
    if not notes:
        raise ValueError(f'No notes in track {midi_song.instruments[track_index]}')
    return midi_song, notes


def best_key(midi_file, track_name='MELODY'):
    """
    Choose best key to play a MIDI song on the EWI

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :return: note string for tonic of key
    """
    best = best_ewi_key(get_notes(midi_file, track_name)[1])
    return midi_2_note(best)

