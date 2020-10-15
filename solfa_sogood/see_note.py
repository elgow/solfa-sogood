import tkinter as tk
from tkinter import font
import rtmidi
import mido
import defopt

try:
    from common import *
except ImportError:
    from .common import *


def main(key_root='C-4'):  # EWI-USB  MidiKeys
    """
    GUI program to monitor a MIDI port and display the last note played as solfa

    :param str key_root: Root note of the major key to use in form e.g. C-3,  Bb-4, D#-3
    :param str port: Name of MIDI port from which to read notes
    """
    LEARN_TEXT = 'Learn Key Root'
    SET_TEXT = 'Set Key Root'

    SHOW_INTERVAL = 30

    root_pitch = current_note = note_2_midi(key_root)
    prev_note = None
    learn_mode = True

    def do_midi(msg_data, client_data):
        nonlocal current_note, solfa_label
        if msg_data:
            msg = mido.parse(msg_data[0])
            if msg.type == MSG.note_on and msg.velocity > 0:
                current_note = msg.note
            elif not learn_mode and (msg.type == MSG.note_off or (msg.type == MSG.note_on and msg.velocity == 0)):
                if msg.note == current_note:
                    current_note = None

    midi_in = rtmidi.MidiIn()
    midi_in.set_callback(do_midi)
        #setCallback(do_midi)
    midi_in.open_port(0) #openPort(0)
    root = tk.Tk()
    root.title('See-Note')

    def close():
        midi_in.closePort()
        root.destroy()


    def set_root():
        nonlocal learn_mode, root_pitch
        if learn_mode:
            root_pitch = current_note
            set_btn.config(text=LEARN_TEXT)
            learn_mode = False
        else:
            set_btn.config(text=SET_TEXT)
            learn_mode = True

    font_fam = 'Arial Black'

    # colored text for solfa notes

    set_btn = tk.Button(root, text='Learn Key Root', command=set_root)

    solfa_label = tk.Label(root, text=midi_to_solfa(current_note, root_pitch), font=font.Font(family=font_fam, size=48),
                           fg=solfa_list[(current_note - root_pitch) % 12][1], width=8)
    solfa_label.pack()
    note_label = tk.Label(root, text='', width=4, font=font.Font(family=font_fam, size=18))
    note_label.pack()
    set_btn.pack(side=tk.LEFT)
    tk.Button(root, text='Quit', command=close).pack(side=tk.RIGHT)

    def show():
        nonlocal prev_note
        if current_note != prev_note:
            active = current_note is not None
            solfa_text = midi_to_solfa(current_note, root_pitch) if active else ''
            text_color = solfa_list[(current_note - root_pitch) % 12][1] if active else 'black'
            note_text = '{0}-{1}'.format(*midi_2_note(current_note)) if active else ''
            solfa_label.config(text=solfa_text, fg=text_color)
            note_label.config(text=note_text)
            prev_note = current_note
        root.after(SHOW_INTERVAL, show)  # reschedule event

    set_root()
    root.after(SHOW_INTERVAL, show)

    root.mainloop()


if __name__ == '__main__':
    defopt.run(main)
