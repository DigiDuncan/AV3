from typing import Literal
import XInput


Button = Literal["a", "b", "x", "y",
                 "left_shoulder", "right_shoulder", "left_thumb", "right_thumb",
                 "start", "back",
                 "dpad_up", "dpad_down", "dpad_left", "dpad_right"]
AnalogInput = Literal["STICK_LEFT", "STICK_RIGHT", "TRIGGER_LEFT", "TRIGGER_RIGHT"]
Input = Button | AnalogInput

UPPER_BUTTONS = ["A", "B", "X", "Y",
                 "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_THUMB", "RIGHT_THUMB",
                 "START", "BACK",
                 "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"]
ANALOGS = ["STICK_LEFT_X", "STICK_RIGHT_X", "STICK_LEFT_Y", "STICK_RIGHT_Y", "TRIGGER_LEFT", "TRIGGER_RIGHT"]
BATTERY_MAP = {"EMPTY": 0, "LOW": 1, "MEDIUM": 2, "FULL": 3}
BUTTON_NAMES = {getattr(XInput, f"BUTTON_{b}"): b.lower() for b in UPPER_BUTTONS}
