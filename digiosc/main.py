from enum import IntEnum
import random

from digiosc.av3.av3 import AV3
from digiosc.lib.logging import setup_logging
from digiosc.lib.types import UNFETCHED, OSCReturnable, ParameterReturnValue, Seconds

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

class Height(IntEnum):
    HEIGHT_UNLOCKED = 50
    HEIGHT_19CM = 42
    HEIGHT_14_5CM = 41
    HEIGHT_12CM = 40
    HEIGHT_9_5CM = 39
    HEIGHT_7_75CM = 38
    HEIGHT_5_5CM = 37
    HEIGHT_4_5CM = 36
    HEIGHT_3_3CM = 35
    HEIGHT_139CM = 51
    HEIGHT_177CM = 52
    HEIGHT_277CM = 54
    HEIGHT_444CM = 56
    HEIGHT_666CM = 58
    HEIGHT_10M = 60
    HEIGHT_13_3M = 61

SCALES = {
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

HEIGHTS = {
    Height.HEIGHT_19CM: 0.19,
    Height.HEIGHT_14_5CM: 0.145,
    Height.HEIGHT_12CM: 0.12,
    Height.HEIGHT_9_5CM: 0.095,
    Height.HEIGHT_7_75CM: 0.0775,
    Height.HEIGHT_5_5CM: 0.055,
    Height.HEIGHT_4_5CM: 0.045,
    Height.HEIGHT_3_3CM: 0.033,
    Height.HEIGHT_139CM: 1.39,
    Height.HEIGHT_177CM: 1.77,
    Height.HEIGHT_277CM: 2.77,
    Height.HEIGHT_444CM: 4.44,
    Height.HEIGHT_666CM: 6.66,
    Height.HEIGHT_10M: 10,
    Height.HEIGHT_13_3M: 13.32
}

def digit(i: int, digit: int) -> int:
    return int(str(i)[digit])

class DigiAV3(AV3):
    """For testing purposes. This is what a user would make."""
    def __init__(self, ip = "127.0.0.1", port = 9000, listen_port = 9001):
        super().__init__(ip, port, listen_port, default_id = 'avtr_5c0e1c16-38ef-4c1d-b8c3-a627c47b07bf', default_height = 1.11,
                         accurate_scale_polling = False, assume_base_state = True,
                         parameter_prefix_blacklist = ("Go/", "VF", "CheeseSync"),
                         verbose = False)

        self.last_shown_height: Seconds = -1
        self.height_show_time = 3.0
        self.last_break = 0.0

        self.scale = 1
        self.force_show = False
        self.broken = False

    def on_start(self):
        self.set_int("Height/DigitA", DASH)
        self.set_int("Height/DigitB", DASH)
        self.set_int("Height/DigitC", DASH)
        self.set_bool("Height/DotA", False)
        self.set_bool("Height/DotB", False)
        self.set_bool("Height/DotC", False)
        self.set_int("Height/Unit", CENTIMETERS)
        self.set_int("Height/Scale", Scale.SCALE_1)
        self.set_bool("Height/Show", False)

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
            print("Avatar was changed to a form!")
            self.on_height_change("FORCED", UNFETCHED)
        else:
            print("Avatar was changed, but not to a form!")

    def on_height_change(self, parameter: str, value: ParameterReturnValue):
        print("OHC")
        if self.broken:
            return
        if "SizeOptions" not in self.custom_parameters or self.custom_parameters["SizeOptions"] == Height.HEIGHT_UNLOCKED:
            if not self.current_height:
                self._set_digits(100000000)
                return
            ch = self.current_height * SCALES[self.custom_parameters["Height/Scale"]]
        else:
            ch = HEIGHTS[self.custom_parameters["SizeOptions"]] * SCALES[self.custom_parameters["Height/Scale"]]

        self.last_shown_height = self.clock
        # NOTE: Current height is in meters.
        print(f"\nCURRENT HEIGHT: {ch:.3f}m")

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
        if parameter == "Height/Scale" or parameter == "SizeOptions":
            self.on_height_change(parameter, value)
        elif parameter == "Height/ForceShow":
            self.force_show = value
            if self.force_show:
                self.set_bool("Height/Show", True)
            else:
                self.set_bool("Height/Show", False)
        elif parameter == "Height/Break":
            self.broken = value
            if not self.broken:
                self.on_height_change("FORCED", None)

    def on_update(self):
        if (self.clock - self.last_shown_height > self.height_show_time) and not self.force_show and self.custom_parameters["Height/Show"] is True:
            self.set_bool("Height/Show", False)
        if self.broken:
            if self.last_break + self.MAX_SPEED < self.clock:
                self._set_digits(random.randrange(0, 999))
                self.last_break = self.clock

    def on_key_press(self, key: str):
        if self.get_paramater_value("Charm/AllowKeyboard"):
            if key == "d":
                self.set_bool("Charm/Left", True)
            elif key == "f":
                self.set_bool("Charm/Down", True)
            elif key == "j":
                self.set_bool("Charm/Up", True)
            elif key == "k":
                self.set_bool("Charm/Right", True)

    def on_key_release(self, key: str):
        if self.get_paramater_value("Charm/AllowKeyboard"):
            if key == "d":
                self.set_bool("Charm/Left", False)
            elif key == "f":
                self.set_bool("Charm/Down", False)
            elif key == "j":
                self.set_bool("Charm/Up", False)
            elif key == "k":
                self.set_bool("Charm/Right", False)

def main():
    setup_logging("digiosc")
    avatar = DigiAV3()
    avatar.start()
