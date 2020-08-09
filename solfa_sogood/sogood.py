from pathlib import Path
from miditoolkit.pianoroll import parser as pp_parser
from miditoolkit import utils as mt_utils
import numpy as np
import defopt
from math import ceil
from io import BytesIO


from bokeh.layouts import column
from bokeh.plotting import figure, show
from bokeh.colors import Color, RGB
from bokeh.io.output import output_file



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

    vol_proll = pp_parser.notes2pianoroll(notes, to_sparse=False).T[low:high]

    # background color indicators, 12 = white keys, 13 = black keys
    bg = np.array([(13 if black_key[(x + low - best) % 12] else 12) for x in range(vol_proll.shape[0])])
    fg = np.array([(x + low - best) % 12 for x in range(vol_proll.shape[0])])

    # init array with black and white key bg vals
    proll = np.empty(vol_proll.shape)
    for r in range(proll.shape[0]):
        proll[r] = np.where(black_key[(r + low - best) % len(black_key)], 13, 12)
        proll[r] = np.where(vol_proll[r] > 0, (r + low - best) % 12, proll[r])



    # set up staffs
    num_staffs = ceil((play_stop - play_start) / (ticks_per_measure * MEASURES_PER_STAFF))

    y_labels = [midi_to_solfa(x, best) for x in range(low, high)]

    staff_ticks = MEASURES_PER_STAFF * ticks_per_measure

    figs = []

    for staff_num in range(num_staffs):
        staff_start = play_start + staff_ticks * staff_num
        f = figure(y_range=y_labels, tools=[])
        f.plot_height = (high - low) * 14
        f.plot_width = MEASURES_PER_STAFF * 180
        f.image(image=[proll[:, staff_start : staff_start + staff_ticks]],
                x=0, y=0, dw=staff_ticks, dh=high - low, palette=list(solfa.values()) + bg_colors)
        figs.append(f)


    def x_tick_label(i, pos):
        return int((i - start_tick) / ticks_per_measure)

    layout = column(*figs)
    # set_title('{} (Do = {}-{})'.format(Path(midi_file).name, *midi_2_note(best)))

    output_file('/tmp/sogood.html')
    show(layout)

if __name__ == '__main__':
    print(defopt.run([best_key, show_score]))
