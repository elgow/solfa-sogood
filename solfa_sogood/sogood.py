from pathlib import Path
from miditoolkit.midi import parser as mid_parser
from numpy import array
import defopt

CHROMATIC_SCALE = ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')
NOTE_NAME_MAP = {**{x: x for x in CHROMATIC_SCALE},
                 **{'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#', 'G#': 'Ab', 'A#': 'Bb'}}

MAJOR_INTERVALS = (2, 2, 1, 2, 2, 2, 1)
MAJOR_RANGE = (0, 2, 4, 5, 7, 9, 11)   # Offsets from tonic for major scale, wraps mod 8 and adds 12 at wrap
EWI_RANGE = (-2, -1) + MAJOR_RANGE + (10, 12, 14, 15)  # range of notes EWI can play w/o octave shift. Bb is easy

# solfa scale note names
solfa = 'Do di Re ri Mi Fa fi So si La li Ti'.split()


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


def _best_ewi_key(notes: {int}):
    """
    Find best key for EWI to play a song consisting of the set of pitches. Consider lowest note in song thru
    median note in song as tonic.

    :param notes: list of Note
    :return: MIDI pitch for tonic of key
    """

    pitches = [x.pitch for x in notes]
    pitchset = set(pitches)
    scores = {}
    for pitch in range(min(pitches), list(pitches)[len(pitches)//2]):
        ewi_scale = set(ewi_range(pitch))
        score = ((10.0 * len(ewi_scale & pitchset)
                 + len([n for n in pitchset if min(ewi_scale) <= n <= max(ewi_scale)])) / len(pitchset)
                 + 10.0 * len([x for x in pitches if x in ewi_scale]) / len(pitches))
        scores[score] = pitch
    return scores[max(scores.keys())]

def midi_to_solfa(midi_pitch, root_pitch):
    """
    Convert a MIDI pitch to solfa for a given scale root
    :param int midi_pitch: played note
    :param int root_pitch: root pitch
    :return: solfa note name
    """
    note = solfa[(midi_pitch - root_pitch) % 12]
    octave = round(((midi_pitch - root_pitch) - 5.9) / 12)
    return (f'{"<" * -octave} {note} {">" * octave}')


def main(midi_file, track_name='MELODY'):
    """
    Choose best key to play a MIDI song on the EWI

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :return: note string for tonic of key
    """
    midi_path = Path(midi_file)
    midi_song = mid_parser.MidiFile(midi_file)
    if len(midi_song.instruments) == 1:
        track_index = 0
    else:
        track_map = {name: num for num, name in enumerate([t.name for t in midi_song.instruments])}
        track_index = track_map.get(track_name)
    notes = midi_song.instruments[track_index].notes
    best = _best_ewi_key(notes)
    stats = [len(x) for x in ((ewi_range(best) & set([x.pitch for x in notes])), set([x.pitch for x in notes]) - ewi_range(best))]

    print(midi_2_note(best), stats)


if __name__ == '__main__':
    defopt.run(main)
