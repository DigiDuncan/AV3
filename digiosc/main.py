import random

from digiosc.av3 import AV3Base
from digiosc.av3.av3 import AV3
from digiosc.lib.logging import setup_logging
from digiosc.lib.types import UNFETCHED, OSCReturnable, Seconds

DASH = 10
OFF = 11

MILLIMETERS = 0
CENTIMETERS = 1
METERS = 2
KILOMETERS = 3

SCALE_1 = 0
SCALE_10 = 1
SCALE_20 = 2
SCALE_100 = 3
SCALE_1000 = 4
SCALE_1_10 = 5
SCALE_1_20 = 6
SCALE_1_100 = 7

SCALES = {
    SCALE_1: 1,
    SCALE_10: 10,
    SCALE_20: 20,
    SCALE_100: 100,
    SCALE_1000: 1000,
    SCALE_1_10: 1/10,
    SCALE_1_20: 1/20,
    SCALE_1_100: 1/100
}

def digit(i: int, digit: int) -> int:
    return int(str(i)[digit])

class DigiAV3(AV3):
    """For testing purposes. This is what a user would make."""
    def __init__(self, ip = "127.0.0.1", port = 9000, listen_port = 9001):
        super().__init__(ip, port, listen_port, default_id = 'avtr_ab4e71a3-36b1-4470-a0c8-a9c007352a15', default_height = 1.11,
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
        self.set_int("Height/Scale", SCALE_1)
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
            self.on_height_change("FORCED", UNFETCHED)

    def on_height_change(self, parameter: str, value: OSCReturnable):
        if self.broken:
            return
        if not self.current_height:
            self._set_digits(100000000)
            return

        self.last_shown_height = self.clock
        # NOTE: Current height is in meters.

        ch = self.current_height * SCALES[self.custom_parameters["Height/Scale"]]
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
        if parameter == "Height/Scale":
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
        if key == "d":
            self.set_bool("Charm/Left", True)
        elif key == "f":
            self.set_bool("Charm/Down", True)
        elif key == "j":
            self.set_bool("Charm/Up", True)
        elif key == "k":
            self.set_bool("Charm/Right", True)

    def on_key_release(self, key: str):
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
