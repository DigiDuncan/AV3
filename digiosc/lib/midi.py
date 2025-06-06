# https://gist.github.com/devxpy/063968e0a2ef9b6db0bd6af8079dad2a
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generator, Literal, TypedDict, Union
import mido

INSTRUMENTS = [
    'Acoustic Grand Piano',
    'Bright Acoustic Piano',
    'Electric Grand Piano',
    'Honky-tonk Piano',
    'Electric Piano 1',
    'Electric Piano 2',
    'Harpsichord',
    'Clavi',
    'Celesta',
    'Glockenspiel',
    'Music Box',
    'Vibraphone',
    'Marimba',
    'Xylophone',
    'Tubular Bells',
    'Dulcimer',
    'Drawbar Organ',
    'Percussive Organ',
    'Rock Organ',
    'Church Organ',
    'Reed Organ',
    'Accordion',
    'Harmonica',
    'Tango Accordion',
    'Acoustic Guitar (nylon)',
    'Acoustic Guitar (steel)',
    'Electric Guitar (jazz)',
    'Electric Guitar (clean)',
    'Electric Guitar (muted)',
    'Overdriven Guitar',
    'Distortion Guitar',
    'Guitar harmonics',
    'Acoustic Bass',
    'Electric Bass (finger)',
    'Electric Bass (pick)',
    'Fretless Bass',
    'Slap Bass 1',
    'Slap Bass 2',
    'Synth Bass 1',
    'Synth Bass 2',
    'Violin',
    'Viola',
    'Cello',
    'Contrabass',
    'Tremolo Strings',
    'Pizzicato Strings',
    'Orchestral Harp',
    'Timpani',
    'String Ensemble 1',
    'String Ensemble 2',
    'SynthStrings 1',
    'SynthStrings 2',
    'Choir Aahs',
    'Voice Oohs',
    'Synth Voice',
    'Orchestra Hit',
    'Trumpet',
    'Trombone',
    'Tuba',
    'Muted Trumpet',
    'French Horn',
    'Brass Section',
    'SynthBrass 1',
    'SynthBrass 2',
    'Soprano Sax',
    'Alto Sax',
    'Tenor Sax',
    'Baritone Sax',
    'Oboe',
    'English Horn',
    'Bassoon',
    'Clarinet',
    'Piccolo',
    'Flute',
    'Recorder',
    'Pan Flute',
    'Blown Bottle',
    'Shakuhachi',
    'Whistle',
    'Ocarina',
    'Lead 1 (square)',
    'Lead 2 (sawtooth)',
    'Lead 3 (calliope)',
    'Lead 4 (chiff)',
    'Lead 5 (charang)',
    'Lead 6 (voice)',
    'Lead 7 (fifths)',
    'Lead 8 (bass + lead)',
    'Pad 1 (new age)',
    'Pad 2 (warm)',
    'Pad 3 (polysynth)',
    'Pad 4 (choir)',
    'Pad 5 (bowed)',
    'Pad 6 (metallic)',
    'Pad 7 (halo)',
    'Pad 8 (sweep)',
    'FX 1 (rain)',
    'FX 2 (soundtrack)',
    'FX 3 (crystal)',
    'FX 4 (atmosphere)',
    'FX 5 (brightness)',
    'FX 6 (goblins)',
    'FX 7 (echoes)',
    'FX 8 (sci-fi)',
    'Sitar',
    'Banjo',
    'Shamisen',
    'Koto',
    'Kalimba',
    'Bag pipe',
    'Fiddle',
    'Shanai',
    'Tinkle Bell',
    'Agogo',
    'Steel Drums',
    'Woodblock',
    'Taiko Drum',
    'Melodic Tom',
    'Synth Drum',
    'Reverse Cymbal',
    'Guitar Fret Noise',
    'Breath Noise',
    'Seashore',
    'Bird Tweet',
    'Telephone Ring',
    'Helicopter',
    'Applause',
    'Gunshot'
]
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(NOTES)

errors = {
    'program': 'Bad input, please refer this spec-\n'
               'http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/program_change.htm',
    'notes': 'Bad input, please refer this spec-\n'
             'http://www.electronics.dit.ie/staff/tscarff/Music_technology/midi/midi_note_numbers_for_octaves.htm'
}


def instrument_to_program(instrument: str) -> int:
    if instrument not in INSTRUMENTS:
        raise ValueError(errors['program'])
    return INSTRUMENTS.index(instrument) + 1


def program_to_instrument(program: int) -> str:
    if not (1 <= program <= 128):
        raise ValueError(errors['program'])
    return INSTRUMENTS[program - 1]


def number_to_note(number: int) -> tuple:
    octave = number // NOTES_IN_OCTAVE
    if octave not in OCTAVES or not (0 <= number <= 127):
        raise ValueError(errors['notes'])
    note = NOTES[number % NOTES_IN_OCTAVE]
    return note, octave


def note_to_number(note: str, octave: int) -> int:
    if note not in NOTES or octave not in OCTAVES:
        raise ValueError(errors['notes'])
    note_i = NOTES.index(note)
    note_i += (NOTES_IN_OCTAVE * octave)
    if not (0 <= note_i <= 127):
        raise ValueError(errors['notes'])
    return note_i

class MIDIPort:
    PORT_OPEN = False

    # It's a singleton!
    def __new__(cls, *args):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MIDIPort, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not self.PORT_OPEN:
            try:
                self.port: mido.ports.IOPort = mido.open_ioport()
                self.PORT_OPEN = True
            except OSError:
                return

    def __iter__(self):
        return self.port.__iter__()

    @property
    def iter_pending(self) -> Callable[[], Generator[MIDIMessage, Any, None]]:
        return self.port.iter_pending

    @property
    def receive(self):
        return self.port.receive

    def close(self):
        self.port.close()

Channel = int
Control = int
Note = int
Program = int

class NoteMessage(TypedDict):
    type: Literal['note_on', 'note_off']
    time: Literal[0]
    note: Note
    velocity: int
    channel: Channel


class ControlMessage(TypedDict):
    type: Literal['control_change']
    time: Literal[0]
    control: Control
    value: int
    channel: Channel


class ProgramMessage(TypedDict):
    type: Literal['program_change']
    time: Literal[0]
    program: Program
    channel: Channel


class PitchWheelMessage(TypedDict):
    type: Literal['pitchwheel']
    time: Literal[0]
    channel: Channel
    pitch: int

MIDIMessage = Union[NoteMessage, ControlMessage, PitchWheelMessage, ProgramMessage]
