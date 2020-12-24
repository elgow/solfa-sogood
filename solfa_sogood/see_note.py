import tkinter as tk
from tkinter import font
import rtmidi
import mido
import defopt
import logging

try:
    from common import *
except ImportError:
    from .common import *


def main(key_root='C-4', *, debug=False):  # EWI-USB  MidiKeys
    """
    GUI program to monitor a MIDI port and display the last note played as solfa

    :param str key_root: Root note of the major key to use in form e.g. C-3,  Bb-4, D#-3
    :param bool debug: debug mode
    """
    LEARN_TEXT = 'Learn Key Root'
    SET_TEXT = 'Set Key Root'

    SHOW_INTERVAL = 100

    log = logging.getLogger(__file__)
    logging.basicConfig()
    log.setLevel(logging.DEBUG if debug else logging.INFO)

    root_pitch = prev_note = current_note = note_2_midi(key_root)
    learn_mode = True

    # UI root
    root = tk.Tk()
    root.title('See-Note')

    def do_midi(msg_data, client_data):
        nonlocal current_note, prev_note
        if msg_data:
            msg = mido.parse(msg_data[0])
            if msg and msg.type in (MSG.note_on, MSG.note_off):
                if msg.type == MSG.note_on and msg.velocity > 0:
                    log.debug(f'note_on {msg.note}')
                    prev_note = current_note
                    current_note = msg.note
                elif not learn_mode and (msg.type == MSG.note_off or (msg.type == MSG.note_on and msg.velocity == 0)):
                    log.debug(f'note_off {msg.note}')
                    if msg.note == current_note:
                        prev_note = current_note
                        current_note = None
                show(current_note)

    # configure RTmidi
    midi_in = rtmidi.MidiIn()
    midi_in.set_callback(do_midi)
    midi_in.open_port(0)

    def close():
        midi_in.close_port()
        root.destroy()


    def set_root_pitch():
        nonlocal learn_mode, root_pitch
        display_note = current_note or prev_note
        if learn_mode:
            root_pitch = display_note
            log.debug(f'root set to {root_pitch}')
            set_btn.config(text=LEARN_TEXT)
            learn_mode = False
        else:
            set_btn.config(text=SET_TEXT)
            learn_mode = True
        show(display_note)

    set_btn = tk.Button(root, text='Learn Key Root', command=set_root_pitch)

    font_fam = 'Arial Black'
    solfa_label = tk.Label(root, text=midi_to_solfa(current_note, root_pitch), font=font.Font(family=font_fam, size=48),
                           fg=solfa_list[(current_note - root_pitch) % 12][1], width=8)
    solfa_label.pack()
    note_label = tk.Label(root, text='', width=4, font=font.Font(family=font_fam, size=18))
    note_label.pack()
    set_btn.pack(side=tk.LEFT)
    tk.Button(root, text='Quit', command=close).pack(side=tk.RIGHT)

    def show(display_note):
        log.debug(f'showing {display_note}')
        solfa_text = midi_to_solfa(display_note, root_pitch) if display_note else ''
        text_color = solfa_list[(display_note - root_pitch) % 12][1] if display_note else 'black'
        note_text = '{0}-{1}'.format(*midi_2_note(display_note)) if display_note else ''
        solfa_label.config(text=solfa_text, fg=text_color)
        note_label.config(text=note_text)

    set_root_pitch()
    root.mainloop()


if __name__ == '__main__':
    defopt.run(main)
