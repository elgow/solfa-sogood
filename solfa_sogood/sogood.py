from pathlib import Path
from itertools import zip_longest
from collections import OrderedDict
from miditoolkit.midi import parser as mid_parser
from miditoolkit.pianoroll import parser as pp_parser
from miditoolkit import utils as mt_utils
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import ticker
import matplotlib.patches as mpatches
from matplotlib.text import Text
import defopt
from math import ceil

try:
    from common import *
except:
    from .common import *


cmap = ListedColormap(list(solfa.values()) + bg_colors)

def show_score(midi_file, track_name='MELODY', *, start=0, end=0, key=None):
    """
    Display MIDI track as pianoroll with solfa notes

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :param str key: name of key to use. Automatically determined if not specified.
    :param int start: number of first measure to display
    :param int end: number of last measure to display

    """
    plt.switch_backend('pdf')
    print(plt.get_backend())


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

    vol_proll = pp_parser.notes2pianoroll(notes, to_sparse=False).T[low:high, :]

    # background color indicators, 12 = white keys, 13 = black keys
    bg = np.array([(13 if key_color[(x + low - best) % 12] else 12) for x in range(vol_proll.shape[0])])
    fg = np.array([(x + low - best) % 12 for x in range(vol_proll.shape[0])])

    proll = np.where(np.where(vol_proll > 0, True, False), fg[:, None], bg[:, None])

    num_staffs = ceil((play_stop - play_start) / (ticks_per_measure * MEASURES_PER_STAFF))
    fig, axs = plt.subplots(nrows=num_staffs, figsize=(MEASURES_PER_STAFF, 1.5 * num_staffs), dpi=300)

    axs[0].set_title('{} (Do = {}-{})'.format(Path(midi_file).name, *midi_2_note(best)))

    y_repeat = 1

    for idx, ax in enumerate(axs):
        def y_tick_label(i, pos):
            return midi_to_solfa(i + low, best)

        ax.yaxis.set_major_formatter(ticker.FuncFormatter(y_tick_label))
        ax.set_yticks([i for i in range(proll.shape[0]) if fg[i] == 12])
        ax.set_yticks([i for i in range(proll.shape[0]) if fg[i] == 13], minor=True)

        def x_tick_label(i, pos):
            return int((i - start_tick) / ticks_per_measure)

        ax.xaxis.set_minor_locator(ticker.IndexLocator(base=midi.ticks_per_beat, offset=0))
        ax.xaxis.set_major_locator(ticker.IndexLocator(base=ticks_per_measure, offset=0))
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(x_tick_label))
        ax_start = play_start + idx * MEASURES_PER_STAFF * ticks_per_measure
        ax.set_xlim([ax_start, ax_start + MEASURES_PER_STAFF * ticks_per_measure])
        ax.xaxis.grid(linestyle='-', linewidth=2, which='major')
        ax.xaxis.grid(color='#e6e6e6', linestyle=':', linewidth=1, which='minor')

        ax.imshow(np.repeat(proll[:, :], y_repeat, axis=0),
                cmap=cmap,
                aspect="auto",
                origin="lower",
                interpolation="none")

    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages('/Volumes/Users/Home/Ed/test.pdf') as export_pdf:
        export_pdf.savefig(dpi=300)

if __name__ == '__main__':
    print(defopt.run([best_key, show_score]))
