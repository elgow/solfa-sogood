from pathlib import Path
from miditoolkit.pianoroll import parser as pp_parser
from miditoolkit import utils as mt_utils
import numpy as np
import defopt
from math import ceil
from io import BytesIO

import pygal
from lxml import etree
from lxml.html import open_in_browser


try:
    from common import *
except:
    from .common import *

DOT_SIZE = 10

cmap =list(solfa.values()) + bg_colors

def show_score(midi_file, track_name='MELODY', *, start=0, end=0, key=None):
    """
    Display MIDI track as pianoroll with solfa notes

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :param str key: name of key to use. Automatically determined if not specified.
    :param int start: number of first measure to display
    :param int end: number of last measure to display

    """

    midi, notes = get_notes(midi_file, track_name)
    best = note_2_midi(key) if key else best_ewi_key(notes)

    ticks_per_measure = midi.ticks_per_beat * midi.time_signature_changes[0].numerator
    start_tick = int(notes[0].start / ticks_per_measure) * ticks_per_measure
    stop_tick = ceil(notes[-1].end / ticks_per_measure) * ticks_per_measure

    play_start = int(start_tick + ticks_per_measure * start)
    play_stop = int(start_tick + ticks_per_measure * end) if end else stop_tick
    MEASURES_PER_STAFF = min(12, ceil((play_stop - play_start) / ticks_per_measure / 4))

    pitches = [x.pitch for x in notes]
    low = min(pitches) - 2
    high = max(pitches) + 2

    vol_proll = pp_parser.notes2pianoroll(notes, to_sparse=False).T

    # background color indicators, 12 = white keys, 13 = black keys
    bg = np.array([(13 if key_color[(x + low - best) % 12] else 12) for x in range(vol_proll.shape[0])])
    fg = np.array([(x + low - best) % 12 for x in range(vol_proll.shape[0])])

    proll = np.where(vol_proll > 0, DOT_SIZE, 0)

    # for i in range(proll.shape[0]):
    #     def f(x):
    #         return i % 2 + 12 if x == 0 else ((i + low - best) % 12)  # white/gray for bg else solfa num val
    #     proll[i] = np.array([f(xi) for xi in proll[i]])
    # proll = proll[low - 2:high + 2, :]

    num_staffs = ceil((play_stop - play_start) / (ticks_per_measure * MEASURES_PER_STAFF))

    # set_title('{} (Do = {}-{})'.format(Path(midi_file).name, *midi_2_note(best)))

    root = etree.Element('root')
    staff_ticks = MEASURES_PER_STAFF * ticks_per_measure

    for staff_num in range(num_staffs):
        chart = pygal.Dot(height=(high - low) * 12)

        for note in range(high, low, -1):
            staff_start = play_start + staff_num * staff_ticks
            points = proll[note, staff_start : staff_start + staff_ticks]

            chart.add(midi_to_solfa(note, best), points)

        root.append(chart.render_tree())


        def y_tick_label(i, pos):
            return midi_to_solfa(i + low, best)

        def x_tick_label(i, pos):
            return int((i - start_tick) / ticks_per_measure)

    open_in_browser(root)

if __name__ == '__main__':
    print(defopt.run([best_key, show_score]))
