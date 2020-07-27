import tkinter as tk
from tkinter import font
import rtmidi
from mingus.core import scales, notes
import defopt

# solfa scale note names
solfa = 'Do di Re ri Mi Fa fi So si La li Ti'.split()

# chromatic scale for one octave to map MIDI pitches
NOTES = ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')

def note_to_midi(midstr):
    """
    Convert note string to MIDI pitch value

    :param str midstr: Note as string in the form C#-4, Db-4, or F-3
    :return: MIDI note value
    """
    parts = midstr.strip().split('-')
    note_num = notes.note_to_int(parts[0])
    return note_num + 12 * (int(parts[1]) + 1)


def midi_to_note(midi_pitch, root_pitch=36):
    """
    Convert a MIDI pitch number to a (Note, Octave) tuple, optionally offsetting octave by some root pitch

    :param int midi_pitch: MIDI pitch
    :param int root_pitch: MIDI pitch for reference octave
    :return: tuple of  (note_name, octave)
    """

    note = ((midi_pitch - 24) % 12)
    octave = int(midi_pitch / 12) - 1

    return (NOTES[note], octave)


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

def main(key_root='C-4'):  # EWI-USB  MidiKeys
    """
    GUI program to monitor a MIDI port and display the last note played as solfa

    :param str key_root: Root note of the major key to use in form e.g. C-3,  Bb-4, D#-3
    :param str port: Name of MIDI port from which to read notes
    """
    LEARN_TEXT = 'Learn Key Root'
    SET_TEXT = 'Set Key Root'

    root_pitch = current_note = note_to_midi(key_root)
    learn_mode = True
    midi_in = rtmidi.RtMidiIn()
    midi_in.openPort(0)
    root = tk.Tk()
    root.title('See-Note')

    def close():
        midi_in.closePort()
        root.destroy()


    def set_root():
        nonlocal learn_mode, root_pitch
        if learn_mode:
            root_pitch = current_note
            show(True)
            set_btn.config(text=LEARN_TEXT)
            learn_mode = False
        else:
            set_btn.config(text=SET_TEXT)
            show(True)
            learn_mode = True

    set_btn = tk.Button(root, text='Learn Key Root', command=set_root)


    font_fam = 'Arial Black'
    solfa_label = tk.Label(root, text='', width=8, font=font.Font(family=font_fam, size=48))
    solfa_label.pack()
    note_label = tk.Label(root, text='', width=4, font=font.Font(family=font_fam, size=18))
    note_label.pack()
    set_btn.pack(side=tk.LEFT)
    tk.Button(root, text='Quit', command=close).pack(side=tk.RIGHT)

    def show(active):
        solfa_text = midi_to_solfa(current_note, root_pitch) if active else ''
        note_text = '{0}-{1}'.format(*midi_to_note(current_note)) if active else ''
        solfa_label.config(text=solfa_text)
        note_label.config(text=note_text)
            
    def do_midi():
        nonlocal current_note, solfa_label
        msg = midi_in.getMessage(250)
        if msg:
            if msg.isNoteOn() and msg.getVelocity() > 0:
                current_note = msg.getNoteNumber()
                show(True)
            elif msg.isNoteOff() and not learn_mode:
                if msg.getNoteNumber() == current_note:
                    show(False)

        #print(msg)
        root.after(2, do_midi)  # reschedule event

    set_root()
    root.after(10, do_midi)

    root.mainloop()


if __name__ == '__main__':
    defopt.run(main)
