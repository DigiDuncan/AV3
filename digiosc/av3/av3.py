from pathlib import Path
import time
from typing import Literal
from digiosc.av3.base import AV3Base
import keyboard
import mouse
import XInput

from digiosc.lib.midi import Channel, MIDIPort, Note, Program
from digiosc.lib.xinput import BUTTON_NAMES, Button

MouseButton = Literal['left', 'middle', 'right', 'x', 'x2']
MouseEventType = Literal['down', 'up', 'double']
LeftOrRight = Literal['left', 'right']

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
        self._warned_about_midi = False
        self._file_handlers: list[Path] = []
        self._file_contents: dict[Path, str] = {}

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
            if not self._warned_about_midi:
                self.logger.error("No open MIDI ports! (MIDI functionality will not work!)")
                self._warned_about_midi = True
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
    
    def _handle_controller(self):
        events = XInput.get_events()
        for e in events:
            controller_id = e.user_index
            match e.type:
                case XInput.EVENT_CONNECTED:
                    self.logger.info(f"Controller ID {e.user_index} connected!")
                case XInput.EVENT_DISCONNECTED:
                    self.logger.error(f"Controller ID {e.user_index} disconnected!")
                case XInput.EVENT_BUTTON_PRESSED:
                    button = BUTTON_NAMES[e.button_id]
                    self._on_button_press(button, controller_id)
                case XInput.EVENT_BUTTON_RELEASED:
                    button = BUTTON_NAMES[e.button_id]
                    self._on_button_release(button, controller_id)
                case XInput.EVENT_STICK_MOVED:
                    stick = "right" if e.stick == XInput.RIGHT else "left"
                    x = e.x
                    y = e.y
                    self._on_stick_move(stick, x, y, controller_id)
                case XInput.EVENT_TRIGGER_MOVED:
                    trigger = "right" if e.trigger == XInput.RIGHT else "left"
                    val = e.value
                    self._on_trigger(trigger, val, controller_id)

    def _handle_files(self):
        for p in self._file_handlers:
            if p not in self._file_contents:
                self._file_contents[p] = ""
            with open(p, encoding = "utf-8") as f:
                contents = f.read().strip()
                if contents != self._file_contents.get(p, ""):
                    self._on_file_changed(p, contents)
                    self._file_contents[p] = contents

    ### PRIVATE VERSIONS OF EVENTS
            
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

    def _on_button_press(self, button: Button, controller_id: int):
        self.on_button_press(button, controller_id)

    def _on_button_release(self, button: Button, controller_id: int):
        self.on_button_release(button, controller_id)

    def _on_stick_move(self, stick: LeftOrRight, x: int, y: int, controller_id: int):
        self.on_stick_move(stick, x, y, controller_id)

    def _on_trigger(self, trigger: LeftOrRight, value: int, controller_id: int):
        self.on_trigger(trigger, value, controller_id)

    def _on_file_changed(self, path: Path, contents: str):
        self.on_file_changed(path, contents)

    def _on_update(self):
        self._last_tick = time.time()
        self._handle_midi()
        self._handle_controller()
        self._handle_files()
        self.on_update()

    ### PUBLIC FUNCTIONS

    def add_file_handler(self, path: Path):
        """Add the path of a file to be listened to for changes."""
        if path not in self._file_handlers:
            self._file_handlers.append(path)

    def remove_file_handler(self, path: Path):
        """Remove a file path from the list of listened-to files."""
        if path in self._file_handlers:
            self._file_handlers.remove(path)

    def start(self):
        super().start()

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

    def on_midi_on(self, note: Note, velocity: int, channel: Channel):
        """Fires when a MIDI note is played."""
        ...
    
    def on_midi_off(self, note: Note, channel: Channel):
        """Fired when a MIDI note is no longer playing."""
        ...

    def on_midi_program_change(self, program: Program, channel: Channel):
        """Fired when a MIDI program changes."""
        ...

    def on_midi_control_change(self, control: Program, channel: Channel):
        """Fired when a MIDI control changes."""
        ...

    def on_midi_pitchweel(self, pitch: int, channel: Channel):
        """Fired when a MIDI pitchwheel is bent."""
        ...

    def on_button_press(self, button: Button, controller_id: int):
        """Fired when a controller button is pressed."""
        ...

    def on_button_release(self, button: Button, controller_id: int):
        """Fired when a controller button is released."""
        ...

    def on_stick_move(self, stick: LeftOrRight, x: int, y: int, controller_id: int):
        """Fired when a controller stick is moved."""
        ...

    def on_trigger(self, trigger: LeftOrRight, value: int, controller_id: int):
        """Fired when a controller trigger is pressed."""
        ...
    
    def on_file_changed(self, path: Path, contents: str):
        """Fired when the contents of a file change.
        Requires the file path be added via `add_file_handler(path: Path)`.
        """
        ...
