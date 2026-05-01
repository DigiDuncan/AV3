import logging
import time
from typing import Iterable, cast

from colored import style
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from digiosc.lib.logging import setup_logging
from digiosc.lib.types import IP, UNFETCHED, Atomic, OSCReturnable, ParameterReturnValue, Port, Position, Rotation, Seconds, UnfetchedType, Velocity
from digiosc.lib.vrchat import AvatarParameters, Gesture, Tracker, TrackingType, Viseme, create_default_parameters_dict, get_default_parameter_names
from digiosc.osc import OSCClient


class AV3Base():
    MAX_SIZE = 256
    BOOL_SIZE = 1
    INT_SIZE = 8
    FLOAT_SIZE = 8

    MIN_INT = 0
    MAX_INT = 255
    MIN_FLOAT = -1.0
    MAX_FLOAT = 1.0

    FLOAT_PREC = 127
    MAX_SPEED = 1 / 10

    DEFAULT_PARAMETER_NAMES = get_default_parameter_names()
    VERBOSE_PARAMETER_NAMES = ("Voice", "Viseme", "AngularY", "VelocityX", "VelocityY", "VelocityZ", "VelocityMagnitude", "Grounded", "Upright", "GestureLeftWeight", "GestureRightWeight")
    VELOCITY_PARAMETER_NAMES = ("VelocityX", "VelocityY", "VelocityZ", "VelocityMagnitude")

    def __init__(self, ip: IP = "127.0.0.1", port: Port = 9000, listen_port: Port = 9001, *,
                 eye_height_factor: float = 1.0,
                 default_id: str | None = None,
                 forms: Iterable[str] | None = None,
                 custom_parameters: dict[str, OSCReturnable] | None = None,
                 assume_base_state: bool = True,
                 parameter_prefix_blacklist: tuple | None = None,
                 round_floats_to: int | None = 3,
                 verbose: bool = False):
        """
        Represents an avatar you can send parameter controls to with OSC, and recieve data from and about.

        - `ip`: The IP to listen/send on.
        - `port`: The sending port.
        - `listen_port`: The listening port.
        - `eye_height_factor` (optional): A number representing the model's true height ratio compared to the
        eye height returned by VRChat. Defaults to 1.0.
        - `default_id` (optional): The ID of the avatar you intend to start in.
        - `forms` (optional): A list of avatar IDs considered to be the same "form" as this one. In theory,
            these should all share a list of parameters.
        - `custom_parameters` (optional): a dictionary of custom parameters on this avatar and their default state.
            - Parameters not in this dictionary will be populated as their updated.
        - `assume_base_state` (optional): sets some assumed base parameters in an attempt to deal with the fact that
            VRChat only sends changes to state.
        - `parameter_prefix_blacklist` (optional): A list of parameter prefixes to ignore when encountered.
        - `round_floats_to` (optional): A decimal amount to round incoming floats to. Defaults to 3, can be None.
        - `verbose`: whether to log spammy parameters, like Viseme or Velocity. `on_parameter_change` will still
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
        ```
        """
        self.ip = ip
        self.port = port
        self.listen_port = listen_port

        self.parameters: AvatarParameters = create_default_parameters_dict()
        self.custom_parameters: dict[str, OSCReturnable] = {}
        self._just_set: list[str] = []
        if custom_parameters:
            self.custom_parameters.update(custom_parameters)
        self.assume_base_state = assume_base_state
        self.parameter_prefix_blacklist = tuple() if parameter_prefix_blacklist is None else parameter_prefix_blacklist
        self.round_floats_to = round_floats_to
        self.verbose = verbose

        self._dispatcher = Dispatcher()
        self._dispatcher.map("/avatar/*", self._handle)
        self._dispatcher.map("/usercamera/*", self._handle)
        self._dispatcher.set_default_handler(self._default_handler)

        self._client = OSCClient(ip, port)
        self._server = BlockingOSCUDPServer((ip, listen_port), self._dispatcher)

        self.current_avatar_id = default_id

        self.current_height: float | UnfetchedType = UNFETCHED
        self.eye_height_factor = eye_height_factor

        self.world_min_height: float = 0.2
        self.world_max_height: float = 5.0
        self.world_allows_scaling: bool = True

        self.forms = () if forms is None else tuple(forms)
        self.forms = set((default_id,) + tuple(self.forms)) if default_id else set(self.forms)
        
        self.logger = logging.getLogger("avatar")
        setup_logging("avatar", logging.INFO, True)

        self._start_time = time.time()
        self._last_tick = time.time()

        self._tracking_type: int | UnfetchedType = UNFETCHED

    @property
    def clock(self) -> float:
        return self._last_tick - self._start_time
    
    def _set_defaults(self):
        self.parameters["Viseme"] = Viseme.SIL
        self.parameters["VelocityMagnitude"] = 0.0
        self.parameters["VelocityX"] = 0.0
        self.parameters["VelocityY"] = 0.0
        self.parameters["VelocityZ"] = 0.0
        self.parameters["Voice"] = 0.0
        self.parameters["Grounded"] = False
        self.parameters["GestureLeft"] = Gesture.NEUTRAL
        self.parameters["GestureRight"] = Gesture.NEUTRAL
        self.parameters["GestureLeftWeight"] = 0.0
        self.parameters["GestureRightWeight"] = 0.0
        self.parameters["Seated"] = False
        self.parameters["InStation"] = False

    def _update_parameter(self, parameter: str, value: OSCReturnable):
        if parameter in self.DEFAULT_PARAMETER_NAMES:
            self.parameters[parameter] = value
            self._on_parameter_change(parameter, value, False, True)
        else:
            self.custom_parameters[parameter] = value
            self._on_parameter_change(parameter, value, True, True)
        self._just_set.append(parameter)

    def set_int(self, parameter: str, value: int):
        """
        Set an integer parameter on an avatar.

        `parameter`: `str`: The name of the parameter.
        `value`: An integer (0 - 255)
        """
        self._client.send_int("/avatar/parameters/" + parameter, value)
        self._update_parameter(parameter, value)
        self.logger.info(f"{self.ip}:{self.port} <- {parameter}: {value}")

    def set_float(self, parameter: str, value: float):
        """
        Set a float parameter on an avatar.

        `parameter`: `str`: The name of the parameter.
        `value`: A float (-1.0 - 1.0)
        """
        self._client.send_float("/avatar/parameters/" + parameter, value)
        self._update_parameter(parameter, value)
        self.logger.info(f"{self.ip}:{self.port} <- {parameter}: {value}")

    def set_bool(self, parameter: str, value: bool):
        """
        Set an boolean parameter on an avatar.

        `parameter`: `str`: The name of the parameter.
        `value`: A boolean.
        """
        self._client.send_bool("/avatar/parameters/" + parameter, value)
        self._update_parameter(parameter, value)
        self.logger.info(f"{self.ip}:{self.port} <- {parameter}: {value}")

    def control_button(self, button: str):
        """Sends a controller input to VRChat."""
        self._client.send_button("/input/" + button)
        self.logger.info(f"{self.ip}:{self.port} <- BUTTON: {button}")

    def control_joystick(self, axis: str, value: float):
        """Sends a controller joystick input to VRChat."""
        self._client.send_float("/input/" + axis, value)
        self.logger.info(f"{self.ip}:{self.port} <- JOYSTICK/{axis}: {value}")

    def message(self, message: str):
        """Sends a generic message to VRChat over OSC."""
        self._client.send_string("/message/", message)
        self.logger.info(f"{self.ip}:{self.port} <- MESSAGE: {message}")

    def set_chatbox_typing(self, state: bool):
        """Set the current typing state on the user. Shows an indicator in-game."""
        self._client.send_bool("/chatbox/typing", state)
        self.logger.info(f"{self.ip}:{self.port} <- TYPING: {state}")

    def send_chatbox_message(self, message: str, immediate: bool = True, sfx: bool = True):
        """Send a message using the in-game chatbox."""
        self._client._send("/chatbox/message", (message, immediate, sfx))
        self.logger.info(f"{self.ip}:{self.port} <- CHATBOX: {message}")

    def set_height(self, height: float, bypass_factor = False):
        """
        Set the avatar's current height. If `bypass_factor` is True, doesn't account for model height
        and sets eye height directly.
        VRChat's allowed range is [0.01-10000], and this function will clamp to those values. 
        """
        if not bypass_factor:
            height /= self.eye_height_factor

        if height < 0.01:
            self.logger.warning(f"Eye height set lower than 1cm ({height:.06f}m). Eye height will be set to 1cm.")
        elif height > 10_000:
            self.logger.warning(f"Eye height set higher than 10km ({height:.06f}m). Eye height will be set to 10km.")
        height = min(10_000, max(0.01, height))
        self._client.send_float("/avatar/eyeheight", height)

    def set_tracker_position(self, tracker: Tracker, position: Position):
        """
        Set the position of the desired tracker.
        https://docs.vrchat.com/docs/osc-trackers
        """
        self._client._send(f"/tracking/trackers/{tracker.value}/position", position)
        if self.verbose:
            self.logger.info(f"{self.ip}:{self.port} <- TRACKER POS: {tracker.name} {position}")

    def set_tracker_rotation(self, tracker: Tracker, rotation: Rotation):
        """
        Set the rotation of the desired tracker.
        https://docs.vrchat.com/docs/osc-trackers
        """
        self._client._send(f"/tracking/trackers/{tracker.value}/rotation", rotation)
        if self.verbose:
            self.logger.info(f"{self.ip}:{self.port} <- TRACKER ROT: {tracker.name} {rotation}")

    def set_head_position(self, position: Position):
        """
        Set the position of the head.
        https://docs.vrchat.com/docs/osc-trackers
        """
        self._client._send("/tracking/trackers/head/position", position)
        if self.verbose:
            self.logger.info(f"{self.ip}:{self.port} <- HEAD POS: {position}")

    def set_head_rotation(self, rotation: Rotation):
        """
        Set the rotation of the head.
        https://docs.vrchat.com/docs/osc-trackers
        """
        self._client._send("/tracking/trackers/head/rotation", rotation)
        if self.verbose:
            self.logger.info(f"{self.ip}:{self.port} <- HEAD ROT: {rotation}")

    # INTERNAL FUNCTIONS

    def _handle(self, address: str, *args: OSCReturnable):
        if address.startswith("/avatar/parameters"):
            endpoint = address.removeprefix("/avatar/parameters/")
            if endpoint.startswith(self.parameter_prefix_blacklist):
                return
            arg = args[0]
            if isinstance(arg, float):
                if self.round_floats_to is not None:
                    arg = round(args[0], self.round_floats_to)
                if endpoint in self.DEFAULT_PARAMETER_NAMES:
                    if self.parameters.get(endpoint, UNFETCHED) == arg:
                        return
                else:
                    if self.custom_parameters.get(endpoint, UNFETCHED) == arg:
                        return
            if endpoint in self.DEFAULT_PARAMETER_NAMES:
                self.parameters[endpoint] = arg
                if (endpoint not in self.VERBOSE_PARAMETER_NAMES) or self.verbose:
                    self.logger.info(f"{self.ip}:{self.listen_port} -> {endpoint}: {arg}")
                if endpoint in self.VELOCITY_PARAMETER_NAMES:
                    if self.parameters["VelocityX"] is not UNFETCHED and self.parameters["VelocityY"] is not UNFETCHED and self.parameters["VelocityZ"] is not UNFETCHED:
                        self._on_velocity_change((self.parameters["VelocityX"], self.parameters["VelocityY"], self.parameters["VelocityZ"]))
                if endpoint == "Viseme":
                    self._on_viseme_change(Viseme(self.parameters["Viseme"]))
                if endpoint == "TrackingType":
                    if self._tracking_type == TrackingType.AV2_HANDS_ONLY and arg != TrackingType.AV2_HANDS_ONLY:
                        self._on_avatar_reset()
                    arg = cast(int, arg)
                    self._tracking_type = arg
            else:
                self.custom_parameters[endpoint] = arg
                if (not endpoint.endswith(('_Angle', "_Stretch", "_Squish"))) or self.verbose:
                    self.logger.info(f"{style.DIM if endpoint in self._just_set else ''}{self.ip}:{self.listen_port} -> CUSTOM {endpoint}: {arg}")  # type: ignore
            self._on_parameter_change(endpoint, arg, endpoint in self.DEFAULT_PARAMETER_NAMES, endpoint in self._just_set)
            if endpoint in self._just_set:
                self._just_set.remove(endpoint)
        elif address == "/avatar/change":
            self.logger.info(f"{self.ip}:{self.listen_port} -> AVATAR CHANGE: {args[0]}")
            id = cast(str, args[0])
            self._on_avatar_change(id, id in self.forms)
        elif address == "/avatar/eyeheight":
            self.logger.info(f"{self.ip}:{self.listen_port} -> AVATAR HEIGHT: {args[0]}")
            height = cast(float, args[0]) * self.eye_height_factor
            self._on_height_change(height)
            self.current_height = height
        elif address == "/avatar/eyeheightmin":
            self.logger.info(f"{self.ip}:{self.listen_port} -> WORLD: Height minimum: {args[0]}")
            height = cast(float, args[0])
            self.world_min_height = height
        elif address == "/avatar/eyeheightmax":
            self.logger.info(f"{self.ip}:{self.listen_port} -> WORLD: Height maximum: {args[0]}")
            height = cast(float, args[0])
            self.world_max_height = height
        elif address == "/avatar/eyeheightscalingallowed":
            self.logger.info(f"{self.ip}:{self.listen_port} -> WORLD: Scaling allowed: {args[0]}")
            allowed = cast(bool, args[0])
            self.world_allows_scaling = allowed
        elif address.startswith("/usercamera"):
            endpoint = address.removeprefix("/usercamera/")
            a = args[0] if len(args) == 1 else args
            self._on_camera_change(endpoint, a)
            self.logger.info(f"{self.ip}:{self.listen_port} -> CAMERA: {endpoint}: {a}")
        else:
            self._on_unknown_message(address, args[0])
            self.logger.warning(f"{self.ip}:{self.listen_port} -> {address}: {args}")

    def _on_avatar_change(self, id: str, is_form: bool):
        self.current_avatar_id = id
        if self.assume_base_state:
            self._set_defaults()
        self.on_avatar_change(id, is_form)

    def _on_avatar_reset(self):
        if self.current_avatar_id in self.forms:
            if self.assume_base_state:
                self._set_defaults()
        self.on_avatar_reset()

    def _on_height_change(self, value: float):
        self.on_height_change(value)

    def _on_parameter_change(self, parameter: str, value: OSCReturnable, custom: bool, set: bool = False):
        self.on_parameter_change(parameter, value, custom, set)

    def _on_velocity_change(self, velocity: Velocity):
        self.on_velocity_change(velocity)

    def _on_viseme_change(self, viseme: Viseme):
        self.on_viseme_change(viseme)

    def _on_camera_change(self, endpoint: str, value: OSCReturnable | tuple[OSCReturnable, ...]):
        self.on_camera_change(endpoint, value)

    def _on_unknown_message(self, address: str, message: Atomic):
        self.on_unknown_message(address, message)

    def _on_update(self):
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        self.on_update(dt)

    def _default_handler(self, address: str, *args: OSCReturnable):
        self.logger.warning(f"{self.ip}:{self.listen_port} -> DEFAULT {address}: {args}")
        self._on_unknown_message(address, args[0])

    # USER-FACING

    def start(self):
        """Start the listening server."""
        self.logger.info(f"Serving on {self.ip}:{self.listen_port}...")
        if self.assume_base_state:
            self._set_defaults()
        self.on_start()
        self._server.service_actions = self._on_update
        self._server.serve_forever(self.MAX_SPEED)

    def get_parameter_value(self, key: str) -> ParameterReturnValue:
        """
        Get the value of the parameter called `key`. Might return UNFETCHED
        if the current state of the parameter is unknown.
        """
        if key not in self.parameters and key not in self.custom_parameters:
            return UNFETCHED
        elif key in self.parameters:
            return self.parameters[key]
        elif key in self.custom_parameters:
            return self.custom_parameters[key]
        return UNFETCHED

    # EVENTS
    def on_avatar_change(self, id: str, is_form: bool) -> None:
        """Fires when a new avatar is loaded. `is_form` is True if the new avatar is in the `forms` list."""
        ...

    def on_avatar_reset(self) -> None:
        """Fires when an avatar is reset."""
        ...

    def on_height_change(self, value: float) -> None:
        """Fires when a message on /avatar/eyeheight is recieved.
        `value` is the value in meters, from 0.01 to 10,000.
        """
        ...

    def on_parameter_change(self, parameter: str, value: OSCReturnable, custom: bool, set: bool) -> None:
        """Fires when a parameter on the avatar changes.
        `custom` is True if this isn't a VRC builtin.
        `set` is True if the parameter change was triggered by a `set_*` function."""
        ...

    def on_velocity_change(self, velocity: Velocity) -> None:
        """Fires when the avatar's velocity changes."""
        ...

    def on_viseme_change(self, viseme: Viseme) -> None:
        """Fires when the avatar's viseme changes."""
        ...

    def on_camera_change(self, endpoint: str, value: OSCReturnable | tuple[OSCReturnable, ...]) -> None:
        """Fires when a setting on the user camera changes."""
        ...

    def on_unknown_message(self, address: str, message: Atomic) -> None:
        """Fires when an unknown OSC message is recieved."""
        ...

    def on_start(self):
        """Fires when the OSC server starts."""
        ...

    def on_update(self, delta_time: Seconds):
        """Fires every tick. (~1/10s) Be careful!"""
        ...
