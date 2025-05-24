from enum import IntEnum
from typing import Literal, TypedDict, get_type_hints

from digiosc.lib.types import UNFETCHED


class Gesture(IntEnum):
    NEUTRAL = 0
    FIST = 1
    HAND_OPEN = 2
    FINGER_POINT = 3
    VICTORY = 4
    ROCK_N_ROLL = MIDDLE_FINGER = 5
    HANDGUN = 6
    THUMBS_UP = 7

class Viseme(IntEnum):
    SIL = 0
    PP = 1
    FF = 2
    TH = 3
    DD = 4
    KK = 5
    CH = 6
    SS = 7
    NN = 8
    RR = 9
    AA = 10
    E = 11
    I = 12  # noqa: E741
    O = 13  # noqa: E741
    U = 14

class TrackingType(IntEnum):
    UNINITALIZED = 0
    GENERIC = 1
    AV2_HANDS_ONLY = 2
    STANDARD = 3
    HIP_TRACKING = 4
    FULL_BODY_NO_HIP = 5
    FULL_BODY = 6

# These are CamelCase because that's what we're going to recieve from OSC
class AvatarParameters(TypedDict):
    IsLocal: bool
    PreviewMode: Literal[0, 1]
    Viseme: Viseme
    Voice: float
    GestureLeft: Gesture
    GestureRight: Gesture
    GestureLeftWeight: float
    GestureRightWeight: float
    AngularY: float
    VelocityX: float
    VelocityY: float
    VelocityZ: float
    VelocityMagnitude: float
    Upright: float
    Grounded: bool
    Seated: bool
    AFK: bool
    TrackingType: TrackingType
    VRMode: Literal[0, 1]  # yep, not a bool, it's an int, who knows
    MuteSelf: bool
    InStation: bool
    Earmuffs: bool
    IsOnFriendsList: bool
    AvatarVersion: Literal[0, 3]  # 3 if AV3, else 0
    IsAnimatorEnabled: bool

    ScaleModified: bool
    ScaleFactor: float
    ScaleFactorInverse: float
    EyeHeightAsMeters: float
    EyeHeightAsPercent: float

def create_default_parameters_dict() -> AvatarParameters:
    r = {}
    for k in get_type_hints(AvatarParameters).keys():
        r[k] = UNFETCHED
    return r

def get_default_parameter_names() -> tuple[str]:
    return tuple(get_type_hints(AvatarParameters))
