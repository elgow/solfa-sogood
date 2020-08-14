from pathlib import Path
import defopt
from math import ceil

from bokeh.layouts import column
from bokeh.plotting import figure, show
from bokeh.colors import Color, RGB
from bokeh.io import output
from bokeh.models import FuncTickFormatter, FixedTicker, ColorBar, LinearColorMapper, Row

try:
    from common import *
except:
    from .common import *

DOT_SIZE = 10

cmap =list(solfa.values()) + bg_colors

def show_score(midi_file, track_name='MELODY', *, start=0, end=0, key=None, dir=Path.home()/'Music/solfa_scores',
               output_file=None):
    """
    Display MIDI track as pianoroll with solfa notes

    :param str midi_file: path to MIDI file as string or Path
    :param str track_name: name of track to use
    :param int start: number of first measure to display
    :param int end: number of last measure to display
    :param str key: name of key to use. Automatically determined if not specified.
    :param str dir: path of dir in which to store output file
    :param str output_file: name of output file (Default: <MIDI file name>.html
    """

    midi, notes = get_notes(midi_file, track_name)
    best = note_2_midi(key) if key else best_ewi_key(notes)




    pitches = {int((x.start + x.end) / 2): x.pitch for x in notes}
    low = min(pitches.values()) - 2
    high = max(pitches.values()) + 2


    ticks_per_measure = midi.ticks_per_beat * midi.time_signature_changes[0].numerator
    start_tick = int(notes[0].start / ticks_per_measure) * ticks_per_measure
    stop_tick = ceil(notes[-1].end / ticks_per_measure) * ticks_per_measure


    measures_per_staff = 8

    # background color indicators, 12 = white keys, 13 = black keys
    # bg = np.array([(13 if black_key[(x + low - best) % 12] else 12) for x in range(vol_proll.shape[0])])
    # fg = np.array([[(x + low - best) % 12] for x in range(vol_proll.shape[0])])

    # init array with black and white key bg vals
    # proll = np.zeros(vol_proll.shape)
    # for r in range(vol_proll.shape[0]):
    #     proll[r] = np.where(vol_proll[r] > 0, fg[r], 13 if black_key[(r + low - best) % 12] else 12)

    # set up staffs
    play_start = start_tick + start * ticks_per_measure
    play_stop = end * ticks_per_measure if end else stop_tick
    num_staffs = ceil((play_stop - play_start) / (ticks_per_measure * measures_per_staff))

    y_labels = ['{}-{}'.format(*midi_2_note(x + 1)) for x in range(low, high)]

    staff_ticks = measures_per_staff * ticks_per_measure

    nan = float('nan')
    figs = []
    for staff_num in range(num_staffs):
        staff_start = play_start + staff_ticks * staff_num
        staff_end = staff_start + staff_ticks
        f = figure(y_range=y_labels, tools=[])
        f.grid.visible = False
        f.yaxis.axis_label_text_baseline = 'top'
        f.plot_height = (high - low) * 12
        f.plot_width = measures_per_staff * 200
        tick_labels = {}
        
        for pitch in range(low + 1, high + 1):
            if black_key[(pitch - best) % 12]:
                f.line([staff_start, staff_end], [pitch - low, pitch - low], line_width=10,
                       alpha=0.5, level='underlay', color=bg_colors[1])
        for tick in range(0, ticks_per_measure * measures_per_staff + 1, midi.ticks_per_beat):
            pos = staff_start + tick
            f.line([pos, pos], [0, high - low], level='underlay',
                   color='gray', line_width=1, alpha=(0.4 if pos % ticks_per_measure else 0.8))

        for note in notes:
            if staff_start <= note.end and note.start <= staff_end:
                tick_labels[int((note.start + note.end) / 2)] = midi_to_solfa(note.pitch, best)
                f.line([max(note.start, staff_start), min(note.end, staff_end)],
                       [note.pitch - low, note.pitch - low],
                       line_width=10, color=list(solfa.values())[(note.pitch - best) % 12], alpha=1.0)

        tick_formatter = FuncTickFormatter(code="""
            var labels = %s;
            return labels[tick];
        """ % tick_labels)
        f.xaxis.ticker = list(tick_labels.keys())
        f.xaxis.formatter = tick_formatter
        figs.append(f)



    # set title and render
    title_text = '{} (Do = {}-{})'.format(Path(midi_file).name, *midi_2_note(best))
    title = figs[0].title
    title.text = title_text
    title.align = "center"
    title.text_color = "gray"
    title.text_font_size = "20px"

    # add colorbar legend for note colors
    color_mapper = LinearColorMapper(palette=list(solfa.values()), low=0, high=len(solfa) - 1)
    color_tick_formatter = FuncTickFormatter(code="""
            var labels = %s;
            return labels[tick];
        """ % list(solfa.keys()))

    color_bar = ColorBar(color_mapper=color_mapper, ticker=FixedTicker(ticks=list(range(len(solfa)))),
                         formatter=color_tick_formatter, border_line_color=None, location=(0, 0))

    figs[0].add_layout(color_bar, 'right')

    layout = column(*figs)

    # make output file
    dir.mkdir(0o755, parents=True, exist_ok=True)
    outfile = str((dir / Path(output_file or midi_file).name).with_suffix('.html'))
    output.output_file(outfile, title=outfile)
    show(layout)

if __name__ == '__main__':
    print(defopt.run([best_key, show_score]))
