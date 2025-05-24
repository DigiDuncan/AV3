import time
from typing import Literal
from digiosc.av3.base import AV3Base
import keyboard
import mouse

from digiosc.lib.midi import Channel, MIDIPort, Note, Program

MouseButton = Literal['left', 'middle', 'right', 'x', 'x2']
MouseEventType = Literal['down', 'up', 'double']

class AV3(AV3Base):
    """Represents an avatar you can send parameter controls to with OSC, and recieve data from and about.
    
    Has additional functions for interfacing with various input devices.
    """
    def __init__(self, ip = "127.0.0.1", port = 9000, listen_port = 9001, *,
                 default_id = None, default_height = None, forms = None,
                 custom_parameters = None,
                 assume_base_state = True,
                 accurate_scale_polling = False,
                 parameter_prefix_blacklist = None,
                 round_floats_to = 3, 
                 verbose = False):
        
        keyboard.hook(self._keyboard_hook)
        mouse.hook(self._mouse_hook)
        self._midi_port = MIDIPort()
        self._warned = False

        super().__init__(ip, port, listen_port,
                         default_id = default_id,
                         default_height = default_height,
                         forms = forms,
                         custom_parameters = custom_parameters,
                         assume_base_state = assume_base_state,
                         accurate_scale_polling = accurate_scale_polling,
                         parameter_prefix_blacklist = parameter_prefix_blacklist,
                         round_floats_to = round_floats_to,
                         verbose = verbose)
        
    def _keyboard_hook(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_DOWN:
            self._on_key_press(event.name)
        elif event.event_type == keyboard.KEY_UP:
            self._on_key_release(event.name)

    def _mouse_hook(self, event: mouse.ButtonEvent | mouse.MoveEvent | mouse.WheelEvent):
        match type(event):
            case mouse.ButtonEvent:
                match event.event_type:
                    case mouse.DOWN:
                        self._on_mouse_press(event.button)
                    case mouse.UP:
                        self._on_mouse_release(event.button)
                    case mouse.DOUBLE:
                        self._on_mouse_double_click(event.button)
            case mouse.MoveEvent:
                self._on_mouse_move(event.x, event.y)
            case mouse.WheelEvent:
                self._on_mouse_scroll(event.delta)

    def _handle_midi(self):
        if not self._midi_port.PORT_OPEN:
            if not self._warned:
                self.logger.error("No open MIDI ports! (MIDI functionality will not work!)")
                self._warned = True
            return
        for msg in self._midi_port.iter_pending():
            match msg['type']:
                case 'note_on':
                    self._on_midi_on(msg['note'], msg['velocity'], msg['channel'])
                case 'note_off':
                    self._on_midi_off(msg['note'], msg['channel'])
                case 'control_change':
                    self._on_midi_control_change(msg['control'], msg['channel'])
                case 'program_change':
                    self._on_midi_control_change(msg['program'], msg['channel'])
                case 'pitchwheel':
                    self._on_midi_pitchweel(msg['pitch'], msg['channel'])
            
    def _on_key_press(self, key: str):
        self.on_key_press(key)
    
    def _on_key_release(self, key: str):
        self.on_key_release(key)

    def _on_mouse_press(self, button: MouseButton):
        self.on_mouse_press(button)

    def _on_mouse_release(self, button: MouseButton):
        self.on_mouse_release(button)
    
    def _on_mouse_double_click(self, button: MouseButton):
        self.on_mouse_double_click(button)

    def _on_mouse_move(self, x: int, y: int):
        self.on_mouse_move(x, y)

    def _on_mouse_scroll(self, delta: float):
        self.on_mouse_scroll(delta)

    def _on_midi_on(self, note: Note, velocity: int, channel: Channel):
        self.on_midi_on(note, velocity, channel)
    
    def _on_midi_off(self, note: Note, channel: Channel):
        self.on_midi_off(note, channel)

    def _on_midi_program_change(self, program: Program, channel: Channel):
        self.on_midi_program_change(program, channel)

    def _on_midi_control_change(self, control: Program, channel: Channel):
        self.on_midi_control_change(control, channel)

    def _on_midi_pitchweel(self, pitch: int, channel: Channel):
        self.on_midi_control_change(pitch, channel)

    def start(self):
        super().start()

    def _on_update(self):
        self._last_tick = time.time()
        self._handle_midi()
        self.on_update()

    ### EVENTS
    def on_key_press(self, key: str):
        """Fires when a key on the keyboard is pressed."""
        ...

    def on_key_release(self, key: str):
        """Fires when a key on the keyboard is released."""
        ...

    def on_mouse_press(self, button: MouseButton):
        """Fires when a mouse button is pressed."""
        ...

    def on_mouse_release(self, button: MouseButton):
        """Fires when a mouse button is released."""
        ...
    
    def on_mouse_double_click(self, button: MouseButton):
        """Fires when a mouse button is double-clicked."""
        ...

    def on_mouse_move(self, x: int, y: int):
        """Fires when the mouse is moved."""
        ...

    def on_mouse_scroll(self, delta: float):
        """Fires when the mouse's scroll wheel is moved."""
        ...

    def _on_midi_on(self, note: Note, velocity: int, channel: Channel):
        """Fires when a MIDI note is played."""
        ...
    
    def _on_midi_off(self, note: Note, channel: Channel):
        """Fired when a MIDI note is no longer playing."""
        ...

    def _on_midi_program_change(self, program: Program, channel: Channel):
        """Fired when a MIDI program changes."""
        ...

    def _on_midi_control_change(self, control: Program, channel: Channel):
        """Fired when a MIDI control changes."""
        ...

    def _on_midi_pitchweel(self, pitch: int, channel: Channel):
        """Fired when a MIDI pitchwheel is bent."""
        ...
