from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Literal, TypedDict, cast, get_type_hints

from digiosc.lib.types import UNFETCHED, float6

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

class CameraMode(IntEnum):
    OFF = 0
    PHOTO = 1
    STREAM = 2
    EMOJI = 3
    MULTILAYER = 4
    PRINT = 5
    DRONE = 6

class Tracker(IntEnum):
    HEAD = 1
    CHEST = 2
    FOOT_L = 3
    FOOT_R = 4
    KNEE_L = 5
    KNEE_R = 6
    ELBOW_L = 7
    ELBOW_R = 8

# These are CamelCase because that's what we're going to recieve from OSC
class AvatarParameters(TypedDict):
    IsLocal: bool
    PreviewMode: Literal[0, 1]  # Will always be 0 from OSC
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
    return cast(AvatarParameters, r)

def get_default_parameter_names() -> tuple[str, ...]:
    return tuple(get_type_hints(AvatarParameters))

class CameraParameters(TypedDict):
    Pose: float6

    # Toggles
    ShowUIInCamera: bool
    LocalPlayer: bool
    RemotePlayer: bool
    Environment: bool
    GreenScreen: bool
    Lock: bool
    SmoothMovement: bool
    LookAtMe: bool
    AutoLevelRoll: bool
    AutoLevelPitch: bool
    Flying: bool
    TriggerTakesPhotos: bool
    DollyPathsStayVisible: bool
    AudioFromCamera: bool
    ShowFocus: bool
    Streaming: bool
    RollWhileFlying: bool
    OrientationIsLandscape: bool

    # Sliders
    Zoom: float
    Exposure: float
    FocalDistance: float
    Aperture: float
    Hue: float
    Saturation: float
    Lightness: float
    LookAtMeXOffset: float
    LookAtMeYOffset: float
    FlySpeed: float
    TurnSpeed: float
    SmoothingStrength: float
    PhotoRate: float
    Duration: float

@dataclass
class CameraSlider:
    address: str
    default: float
    minimum: float
    maximum: float

CAMERA_SLIDERS: dict[str, CameraSlider] = {
    "Zoom": CameraSlider("Zoom", 45, 20, 150),
    "Exposure": CameraSlider("Exposure", 0, -10, 4),
    "FocalDistance": CameraSlider("FocalDistance", 1.5, 0, 10),
    "Aperture": CameraSlider("Aperture", 15, 1.4, 32),
    "Hue": CameraSlider("Hue", 120, 0, 360),
    "Saturation": CameraSlider("Saturation", 100, 0, 100),
    "Lightness": CameraSlider("Lightness", 60, 0, 50),
    "LookAtMeXOffset": CameraSlider("LookAtMeXOffset", 0, -25, 25),
    "LookAtMeYOffset": CameraSlider("LookAtMeYOffset", 0, -25, 25),
    "FlySpeed": CameraSlider("FlySpeed", 3, 0.1, 15),
    "TurnSpeed": CameraSlider("TurnSpeed", 1, 0.1, 5),
    "SmoothingStrength": CameraSlider("SmoothingStrength", 5, 0.1, 10),
    "PhotoRate": CameraSlider("PhotoRate", 1, 0.1, 2),
    "Duration": CameraSlider("Duration", 2, 0.1, 60)
}

class Axis(StrEnum):
    HORIZONTAL = "Horizontal"
    VERTICAL = "Vertical"
    LOOK_HORIZONTAL = "LookHorizontal"
    LOOK_VERTICAL = "LookVertical"
    SPIN_HOLD_CW_CCW = "SpinHoldCwCcw"
    SPIN_HOLD_UD = "SpinHoldUD"
    SPIN_HOLD_LR = "SpinHoldLR"
    MOVE_HOLD_FB = "MoveHoldFB"
    USE_AXIS_RIGHT = "UseAxisRight"
    GRAB_AXIS_RIGHT = "GrabAxisRight"

class Button(StrEnum):
    MOVE_FORWARD = "MoveForward"
    MOVE_BACKWARD = "MoveBackward"
    MOVE_LEFT = "MoveLeft"
    MOVE_RIGHT = "MoveRight"
    LOOK_LEFT = "LookLeft"
    LOOK_RIGHT = "LookRight"
    JUMP = "Jump"
    RUN = "Run"
    COMFORT_LEFT = "ComfortLeft"
    COMFORT_RIGHT = "ComfortRight"
    GRAB_RIGHT = "GrabRight"
    USE_RIGHT = "UseRight"
    DROP_RIGHT = "DropRight"
    GRAB_LEFT = "GrabLeft"
    USE_LEFT = "UseLeft"
    DROP_LEFT = "DropLeft"
    PANIC_BUTTON = "PanicButton"
    QUICK_MENU_TOGGLE_LEFT = "QuickMenuToggleLeft"
    QUICK_MENU_TOGGLE_RIGHT = "QuickMenuToggleRight"
    TOGGLE_SIT_STAND = "ToggleSitStand"
    AFK_TOGGLE = "AFKToggle"
    VOICE = "Voice"
    SHOW_DEBUG_INFO_0 = DEBUG_UI_SHAPES = "ShowDebugInfo0"
    SHOW_DEBUG_INFO_1 = DEBUG_ASSET_BUNDLES = "ShowDebugInfo1"
    SHOW_DEBUG_INFO_2 = DEBUG_FPS_BUILD = "ShowDebugInfo2"
    SHOW_DEBUG_INFO_3 = DEBUG_LOG = "ShowDebugInfo3"
    SHOW_DEBUG_INFO_4 = DEBUG_USER_STATS = "ShowDebugInfo4"
    SHOW_DEBUG_INFO_5 = DEBUG_NETWORKING = "ShowDebugInfo5"
    SHOW_DEBUG_INFO_6 = DEBUG_NETWORKED_OBJECTS = "ShowDebugInfo6"
    SHOW_DEBUG_INFO_7 = DEBUG_PHYSBONES = "ShowDebugInfo7"
    SHOW_DEBUG_INFO_8 = DEBUG_SYNCED_OBJECTS = "ShowDebugInfo8"
    SHOW_DEBUG_INFO_9 = DEBUG_PLAYERS = "ShowDebugInfo9"
