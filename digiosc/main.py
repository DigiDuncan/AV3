from enum import IntEnum
import random
import logging
import time

from digiosc.av3.av3 import AV3
from digiosc.lib.logging import setup_logging
from digiosc.lib.types import ParameterReturnValue, Seconds

logger = logging.getLogger("digiosc")

###
# !: THIS IS IMPORTANT
# THIS IS CODE I AM LITERALLY RUNNING TO TEST THIS LIBRARY
# IT IS NOT A "REFERENCE IMPLEMENTATION"
# IT IS NOT GOOD CODE IN SOME WAYS
# THIS WON'T BE HERE WHEN THE LIBRARY RELEASES
# YOU CAN LOOK AT IT,
# YOU CAN SMELL IT,
# BUT DON'T EXPECT IT TO WORK FOR YOUR USE CASE
###

DASH = 10
OFF = 11
ALL_DASHES = 1e9

MILLIMETERS = 0
CENTIMETERS = 1
METERS = 2
KILOMETERS = 3

class Scale(IntEnum):
    SCALE_1 = 0
    SCALE_5 = 1
    SCALE_10 = 2
    SCALE_20 = 3
    SCALE_50 = 4
    SCALE_100 = 5
    SCALE_1000 = 6
    SCALE_1_5 = 7
    SCALE_1_10 = 8
    SCALE_1_20 = 9
    SCALE_1_50 = 10
    SCALE_1_100 = 11
    SCALE_1_1000 = 12
    SCALE_1_2000 = 13

SCALES: dict[Scale, int | float] = {
    Scale.SCALE_1: 1,
    Scale.SCALE_5: 5,
    Scale.SCALE_10: 10,
    Scale.SCALE_20: 20,
    Scale.SCALE_50: 50,
    Scale.SCALE_100: 100,
    Scale.SCALE_1000: 1000,
    Scale.SCALE_1_5: 1 / 5,
    Scale.SCALE_1_10: 1 / 10,
    Scale.SCALE_1_20: 1 / 20,
    Scale.SCALE_1_50: 1 / 50,
    Scale.SCALE_1_100: 1 / 100,
    Scale.SCALE_1_1000: 1 / 1000,
    Scale.SCALE_1_2000: 1 / 2000,
}

class Speed(IntEnum):
    SPEED_5MM = 0
    SPEED_1CM = 1
    SPEED_2_5CM = 2
    SPEED_5CM = 3
    SPEED_10CM = 4
    SPEED_25CM = 5
    SPEED_50CM = 6

SPEEDS: dict[Speed, int | float] = {
    Speed.SPEED_5MM: 0.005,
    Speed.SPEED_1CM: 0.01,
    Speed.SPEED_2_5CM: 0.025,
    Speed.SPEED_5CM: 0.05,
    Speed.SPEED_10CM: 0.1,
    Speed.SPEED_25CM: 0.25,
    Speed.SPEED_50CM: 0.5,
}

def digit(i: int, digit: int) -> int:
    return int(str(i)[digit])

class DigiAV3(AV3):
    """For testing purposes. This is what a user would make."""
    def __init__(self, ip = "127.0.0.1", port = 9000, listen_port = 9001):
        super().__init__(ip, port, listen_port, default_id = 'avtr_5c0e1c16-38ef-4c1d-b8c3-a627c47b07bf',
                         eye_height_factor = 1.11 / 0.98,
                         assume_base_state = True,
                         parameter_prefix_blacklist = ("Go/", "VF", "CheeseSync", "Cam", "Gesture"),
                         verbose = False)

        self.last_shown_height: Seconds = -1
        self.height_show_time = 3.0
        self.last_break = 0.0

        self.scale = 1
        self.force_show = False
        self.broken = False

        self.last_height_tick: Seconds = -1

    def on_start(self):
        self.set_int("Height/Unit", CENTIMETERS)
        self.set_int("Height/Scale", Scale.SCALE_1)
        self.set_bool("Height/Show", False)
        self.set_int("HeightOSC/Speed", Speed.SPEED_10CM)

    def _set_digits(self, value: float, decimal = 0):
        i = int(value * (10 ** decimal))

        # Numerals
        if len(str(i)) > 3:
            # Too many digits
            self.set_int("Height/DigitA", DASH)
            self.set_int("Height/DigitB", DASH)
            self.set_int("Height/DigitC", DASH)
        elif len(str(i)) == 3:
            # All digits filled
            self.set_int("Height/DigitA", digit(i, 0))
            self.set_int("Height/DigitB", digit(i, 1))
            self.set_int("Height/DigitC", digit(i, 2))
        elif len(str(i)) == 2:
            # Two digits filled
            self.set_int("Height/DigitA", OFF if decimal < 2 else 0)
            self.set_int("Height/DigitB", digit(i, 0))
            self.set_int("Height/DigitC", digit(i, 1))
        else:
            # One digit filled
            self.set_int("Height/DigitA", OFF if decimal < 2 else 0)
            self.set_int("Height/DigitB", OFF if decimal < 1 else 0)
            self.set_int("Height/DigitC", digit(i, 0))

        # Dots
        # This is redundant but JIC we ever use this dot...
        self.set_bool("Height/DotC", False)
        if len(str(i)) > 3 or decimal == 0:
            self.set_bool("Height/DotA", False)
            self.set_bool("Height/DotB", False)
        elif decimal == 1:
            self.set_bool("Height/DotA", False)
            self.set_bool("Height/DotB", True)
        elif decimal == 2:
            self.set_bool("Height/DotA", True)
            self.set_bool("Height/DotB", False)

    def on_avatar_change(self, id, is_form):
        self.force_show = False
        if is_form:
            logger.info("Avatar was changed to a form!")
            self.on_height_change(None)
        else:
            logger.info("Avatar was changed, but not to a form!")

    def on_avatar_reset(self) -> None:
        self.on_height_change(None)

    def on_height_change(self, value: ParameterReturnValue | None):
        if self.broken:
            return
        if not value:
            self._set_digits(ALL_DASHES)
            return
        else:
            ch = value * SCALES[self.custom_parameters["Height/Scale"]]  # type: ignore

        self.last_shown_height = self.clock
        # NOTE: Current height is in meters.
        logger.info(f"\nCURRENT HEIGHT: {ch:.3f}m")

        if ch >= 1000:
            # 1km+
            self.set_int("Height/Unit", KILOMETERS)
            self._set_digits(ch / 1000, 1)
        elif ch >= 100:
            # 100-999m
            self.set_int("Height/Unit", METERS)
            self._set_digits(ch)
        elif ch >= 10:
            # 10-99m
            self.set_int("Height/Unit", METERS)
            self._set_digits(ch, 1)
        elif ch >= 0.1:
            # 10cm-9m
            self.set_int("Height/Unit", CENTIMETERS)
            self._set_digits(ch * 100)
        elif ch >= 0.01:
            # 1cm-9cm
            self.set_int("Height/Unit", CENTIMETERS)
            self._set_digits(ch * 100, 1)
        elif ch >= 0.0001:
            # 0.1mm-9mm
            self.set_int("Height/Unit", MILLIMETERS)
            self._set_digits(ch * 1000, 1)
        else:
            # <0.1mm
            self.set_int("Height/Unit", MILLIMETERS)
            self._set_digits(ch * 1000, 2)

        self.set_bool("Height/Show", True)

    def on_parameter_change(self, parameter, value, custom, set):
        if parameter == "Height/ForceShow":
            self.force_show = value
            if self.force_show:
                self.set_bool("Height/Show", True)
            else:
                self.set_bool("Height/Show", False)
        elif parameter == "Height/Break":
            self.broken = value
            if not self.broken:
                self.on_height_change(None)
        elif parameter == "HeightOSC/Reset" and value:
            self.set_height(1.11)
        elif parameter == "HeightOSC/Up" and value:
            speed = SPEEDS[self.get_parameter_value("HeightOSC/Speed")]
            self.set_height(self.current_height + speed)
        elif parameter == "HeightOSC/Down" and value:
            speed = SPEEDS[self.get_parameter_value("HeightOSC/Speed")]
            self.set_height(self.current_height - speed)
        elif parameter == "HeightOSC/SlowUp" or parameter == "HeightOSC/SlowDown":
            self.last_height_tick = self.clock

    def on_update(self, delta_time: Seconds):
        if (self.clock - self.last_shown_height > self.height_show_time) and not self.force_show and self.get_parameter_value("Height/Show") is True:
            self.set_bool("Height/Show", False)
        if self.broken:
            if self.last_break + self.MAX_SPEED < self.clock:
                self._set_digits(random.randrange(0, 999))
                self.last_break = self.clock

        # HeightOSC
        if (self.last_height_tick + self.MAX_SPEED < self.clock) and self.current_height:
            dt = self.clock - self.last_height_tick
            speed = SPEEDS[self.get_parameter_value("HeightOSC/Speed")]
            if self.get_parameter_value("HeightOSC/SlowUp"):
                self.set_height(self.current_height + (speed * dt))
                self.last_height_tick = self.clock
            elif self.get_parameter_value("HeightOSC/SlowDown"):
                self.set_height(self.current_height - (speed * dt))
                self.last_height_tick = self.clock

    def on_key_press(self, key: str):
        if self.get_parameter_value("Charm/AllowKeyboard"):
            if key == "d":
                self.set_bool("Charm/Left", True)
            elif key == "f":
                self.set_bool("Charm/Down", True)
            elif key == "j":
                self.set_bool("Charm/Up", True)
            elif key == "k":
                self.set_bool("Charm/Right", True)
        if key == "=":
            print(self.custom_parameters)
        elif key == "]":
            self.set_bool("HeightOSC/SlowUp", True)
        elif key == "[":
            self.set_bool("HeightOSC/SlowDown", True)
        elif key == ",":
            self.set_bool("HeightOSC/Down", True)
        elif key == ".":
            self.set_bool("HeightOSC/Up", True)

    def on_key_release(self, key: str):
        if self.get_parameter_value("Charm/AllowKeyboard"):
            if key == "d":
                self.set_bool("Charm/Left", False)
            elif key == "f":
                self.set_bool("Charm/Down", False)
            elif key == "j":
                self.set_bool("Charm/Up", False)
            elif key == "k":
                self.set_bool("Charm/Right", False)
        if key == "]":
            self.set_bool("HeightOSC/SlowUp", False)
        elif key == "[":
            self.set_bool("HeightOSC/SlowDown", False)
        elif key == ",":
            self.set_bool("HeightOSC/Down", False)
        elif key == ".":
            self.set_bool("HeightOSC/Up", False)
def main():
    setup_logging("digiosc")
    avatar = DigiAV3()
    avatar.start()
