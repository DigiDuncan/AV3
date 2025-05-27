from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Literal, Optional
import keyboard
import mouse
import requests
import XInput

from digiosc.av3.base import AV3Base
from digiosc.lib.midi import Channel, MIDIPort, Note, Program
from digiosc.lib.types import URL, Seconds
from digiosc.lib.xinput import BUTTON_NAMES, Button

MouseButton = Literal['left', 'middle', 'right', 'x', 'x2']
MouseEventType = Literal['down', 'up', 'double']
LeftOrRight = Literal['left', 'right']
StringProcessor = Callable[[str], Any]
DictProcessor = Callable[[dict], Any]

@dataclass
class FileHandler:
    path: Path
    poll_time: Seconds
    return_json: bool = False
    processor: Optional[StringProcessor | DictProcessor] = None

@dataclass
class URLHandler:
    url: URL
    poll_time: Seconds
    return_json: bool = False
    processor: Optional[StringProcessor | DictProcessor] = None


class AV3(AV3Base):
    def __init__(self, ip = "127.0.0.1", port = 9000, listen_port = 9001, *,
                 default_id = None, default_height = None, forms = None,
                 custom_parameters = None,
                 assume_base_state = True,
                 accurate_scale_polling = False,
                 parameter_prefix_blacklist = None,
                 round_floats_to = 3, 
                 verbose = False):
        """
        Represents an avatar you can send parameter controls to with OSC, and recieve data from and about.
        
        Has additional functions for interfacing with various input devices.
        `ip`: The IP to listen/send on.
        `port`: The sending port.
        `listen_port`: The listening port.
        `default_id` (optional): The ID of the avatar you intend to start in.
        `default_height` (optional): The height of the default avatar (and all its forms.)
        `forms` (optional): A list of avatar IDs considered to be the same "form" as this one. In theory,
            these should all share a height and list of parameters.
        `custom_parameters` (optional): a dictionary of custom parameters on this avatar and their default state.
            Parameters not in this dictionary will be populated as their updated.
        `assume_base_state` (optional): sets some assumed base parameters in an attempt to deal with the fact that
            VRChat only sends changes to state.
        `accurate_scale_polling` (optional): whether to fire `on_height_change` for all scale-based events (true),
            or only on `ScaleFactor` (false).
        `parameter_prefix_blacklist` (optional): A list of parameter prefixes to ignore when encountered.
        `round_floats_to` (optional): A decimal amount to round incoming floats to. Defaults to 3, can be None.
        `verbose`: whether to log spammy parameters, like Viseme or Velocity. `on_parameter_change` will still
            capture these events.

        Available events:
        ```
        on_start
        on_update
        on_avatar_change
        on_height_change
        on_parameter_change
        on_velocity_change
        on_viseme_change
        on_unknown_message
        on_key_press
        on_key_release
        on_mouse_press
        on_mouse_release
        on_mouse_double_click
        on_mouse_move
        on_mouse_scroll
        on_midi_on
        on_midi_off
        on_midi_program_change
        on_midi_control_change
        on_midi_pitchweel
        on_button_press
        on_button_release
        on_stick_move
        on_trigger
        on_file_changed
        on_url_changed
        ```
        """
        keyboard.hook(self._keyboard_hook)
        mouse.hook(self._mouse_hook)
        self._midi_port = MIDIPort()
        self._warned_about_midi = False

        self._file_handlers: dict[Path, FileHandler] = {}
        self._file_contents: dict[Path, Any] = {}
        self._last_polled_files: dict[Path, Seconds] = {}

        self._url_handlers: dict[str, URLHandler] = {}
        self._url_contents: dict[str, Any] = {}
        self._last_polled_urls: dict[str, Seconds] = {}

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
        for fh in self._file_handlers.values():
            path = fh.path
            _last_polled = self._last_polled_files
            if path in _last_polled and _last_polled[path] + fh.poll_time > self.clock:
                continue

            with open(fh.path, "r", encoding = "utf-8") as f:
                if fh.return_json:
                    contents = json.load(f)
                else:
                    contents = f.read().strip()
            if fh.processor:
                contents = fh.processor(contents)
            _file_contents = self._file_contents
            if fh.path in _file_contents and _file_contents[path] == contents:
                return
            _file_contents[path] = contents
            _last_polled[path] = self.clock
            self._on_file_changed(path, contents)

    def _handle_urls(self):
        for uh in self._url_handlers.values():
            url = uh.url
            _last_polled = self._last_polled_urls
            if url in _last_polled and _last_polled[url] + uh.poll_time > self.clock:
                continue

            r = requests.get(url)
            if r.status_code != 200:
                self.logger.error(f"{url} raised status code {r.status_code}!")
                continue

            if uh.return_json:
                contents = r.json()
            else:
                contents = r.text

            if uh.processor:
                contents = uh.processor(contents)
            _url_contents = self._url_contents
            if uh.url in _url_contents and _url_contents[url] == contents:
                return
            _url_contents[url] = contents
            _last_polled[url] = self.clock
            self._on_url_changed(url, contents)

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

    def _on_file_changed(self, path: Path, contents: Any):
        self.on_file_changed(path, contents)

    def _on_url_changed(self, url: URL, contents: Any):
        self.on_url_changed(url, contents)

    def _on_update(self):
        self._last_tick = time.time()
        self._handle_midi()
        self._handle_controller()
        self._handle_files()
        self._handle_urls()
        self.on_update()

    ### PUBLIC FUNCTIONS

    def add_file_handler(self, path: Path, poll_time: Seconds, return_json: bool = False, processor: StringProcessor | DictProcessor = None):
        """Add the path of a file to be listened to for changes.
        `poll_time: Seconds`: how often to poll this file
        `return_json: bool`: whether or not to return the file as a JSON before processing
        `processor: function`: a function that takes in a string or a dict and returns some data which will then be the
            data provided in the event
        """
        fh = FileHandler(path, poll_time, return_json, processor)
        if path not in self._file_handlers:
            self._file_handlers[path] = fh

    def remove_file_handler(self, path: Path):
        """Remove a file path from the list of listened-to files."""
        if path in self._file_handlers:
            self._file_handlers.pop(path)

    def add_url_handler(self, url: URL, poll_time: Seconds = 60.0, return_json: bool = False, processor: StringProcessor | DictProcessor = None):
        """Add a URL to be listened to for changes.
        `poll_time: Seconds`: how often to poll this URL
        `return_json: bool`: whether or not to return the URL contents as a JSON before processing
        `processor: function`: a function that takes in a string or a dict and returns some data which will then be the
            data provided in the event
        """
        uh = URLHandler(url, poll_time, return_json, processor)
        if url not in self._url_handlers:
            self._url_handlers[url] = uh

    def remove_url_handler(self, url: URL):
        """Remove a URL from the list of listened-to URLs."""
        if url in self._url_handlers:
            self._url_handlers.pop(url)

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
    
    def on_file_changed(self, path: Path, contents: Any):
        """Fired when the contents of a file change.
        Requires the file path be added via `add_file_handler()`.
        """
        ...

    def on_url_changed(self, url: URL, contents: Any):
        """Fired when the contents of a URL endpoint change.
        Requires the URL be added via `add_url_handler()`.
        """
        ...
