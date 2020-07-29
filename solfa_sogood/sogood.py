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

try:
    from common import *
except:
    from .common import *


cmap = ListedColormap(bg_colors + list(solfa.values()))

def show_score(midi_file, track_name='MELODY', key=None):
    """
    Display MIDI track as pianoroll with solfa notes

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :param str key: name of key to use. Automatically determined if not specified.
    """
    notes = get_notes(midi_file, track_name)
    best = note_2_midi(key) if key else best_ewi_key(notes)

    pitches = [x.pitch for x in notes]
    low = min(pitches)
    high = max(pitches)

    proll = pp_parser.notes2pianoroll(notes, to_sparse=False).T

    for i in range(low - 2, high + 2):
        def f(x):
            return i % 2 if x == 0 else ((i - best) % 12) + 2
        proll[i] = np.array([f(xi) for xi in proll[i]])
    # proll = proll[low - 2:high + 2, :]

    fig, ax = plt.subplots()  # Create a figure containing a single axes.
    plt.title(Path(midi_file).name)
    ax.set_yticks(range(proll.shape[0]))
    yticks = plt.yticks()
    tick_dic = dict(zip_longest(list(yticks[0]), yticks[1]))

    for p, l in tick_dic.items():
        text, color = list(solfa.items())[(p - best) % 12]
        l.set_color(color)

    def tick_label(i, pos):
        return midi_to_solfa(i, best)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(tick_label))
    ax.set_ylim([low - 2, high + 2])

    tonic = mpatches.Patch(color=solfa['Do'], label='Do = {}-{}'.format(*midi_2_note(best)))
    plt.legend(handles=[tonic])

    ax.imshow(proll[:, 9000:20000],
            cmap=cmap,
            aspect="auto",
            origin="lower",
            interpolation="none")

    fig.show()
    plt.ion()
    plt.show()

if __name__ == '__main__':
    print(defopt.run([best_key, show_score]))
