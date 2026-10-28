from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Literal, TypedDict, cast, get_type_hints

from digiosc.lib.types import UNFETCHED, float6
from digiosc.lib.utils import clamp

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

    UserEyeTracking: bool
    UserFaceTracking: bool

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

@dataclass
class FullFaceTrackingPayload:
    """Each paramater must be set, and must be a value between 0.0 and 1.0."""
    EyeLookOutRight: float = 0.0
    EyeLookInRight: float = 0.0
    EyeLookUpRight: float = 0.0
    EyeLookDownRight: float = 0.0
    EyeLookOutLeft: float = 0.0
    EyeLookInLeft: float = 0.0
    EyeLookUpLeft: float = 0.0
    EyeLookDownLeft: float = 0.0
    EyeClosedRight: float = 0.0
    EyeClosedLeft: float = 0.0
    EyeDilationRight: float = 0.0
    EyeDilationLeft: float = 0.0
    EyeConstrictRight: float = 0.0
    EyeConstrictLeft: float = 0.0
    EyeSquintRight: float = 0.0
    EyeSquintLeft: float = 0.0
    EyeWideRight: float = 0.0
    EyeWideLeft: float = 0.0
    BrowPinchRight: float = 0.0
    BrowPinchLeft: float = 0.0
    BrowLowererRight: float = 0.0
    BrowLowererLeft: float = 0.0
    BrowInnerUpRight: float = 0.0
    BrowInnerUpLeft: float = 0.0
    BrowOuterUpRight: float = 0.0
    BrowOuterUpLeft: float = 0.0
    NasalDilationRight: float = 0.0
    NasalDilationLeft: float = 0.0
    NasalConstrictRight: float = 0.0
    NasalConstrictLeft: float = 0.0
    CheekSquintRight: float = 0.0
    CheekSquintLeft: float = 0.0
    CheekPuffRight: float = 0.0
    CheekPuffLeft: float = 0.0
    CheekSuckRight: float = 0.0
    CheekSuckLeft: float = 0.0
    JawOpen: float = 0.0
    JawRight: float = 0.0
    JawLeft: float = 0.0
    JawForward: float = 0.0
    JawBackward: float = 0.0
    JawClench: float = 0.0
    JawMandibleRaise: float = 0.0
    MouthClosed: float = 0.0
    LipSuckUpperRight: float = 0.0
    LipSuckUpperLeft: float = 0.0
    LipSuckLowerRight: float = 0.0
    LipSuckLowerLeft: float = 0.0
    LipSuckCornerRight: float = 0.0
    LipSuckCornerLeft: float = 0.0
    LipFunnelUpperRight: float = 0.0
    LipFunnelUpperLeft: float = 0.0
    LipFunnelLowerRight: float = 0.0
    LipFunnelLowerLeft: float = 0.0
    LipPuckerUpperRight: float = 0.0
    LipPuckerUpperLeft: float = 0.0
    LipPuckerLowerRight: float = 0.0
    LipPuckerLowerLeft: float = 0.0
    MouthUpperUpRight: float = 0.0
    MouthUpperUpLeft: float = 0.0
    MouthUpperDeepenRight: float = 0.0
    MouthUpperDeepenLeft: float = 0.0
    NoseSneerRight: float = 0.0
    NoseSneerLeft: float = 0.0
    MouthLowerDownRight: float = 0.0
    MouthLowerDownLeft: float = 0.0
    MouthUpperRight: float = 0.0
    MouthUpperLeft: float = 0.0
    MouthLowerRight: float = 0.0
    MouthLowerLeft: float = 0.0
    MouthCornerPullRight: float = 0.0
    MouthCornerPullLeft: float = 0.0
    MouthCornerSlantRight: float = 0.0
    MouthCornerSlantLeft: float = 0.0
    MouthFrownRight: float = 0.0
    MouthFrownLeft: float = 0.0
    MouthStretchRight: float = 0.0
    MouthStretchLeft: float = 0.0
    MouthDimpleRight: float = 0.0
    MouthDimpleLeft: float = 0.0
    MouthRaiserUpper: float = 0.0
    MouthRaiserLower: float = 0.0
    MouthPressRight: float = 0.0
    MouthPressLeft: float = 0.0
    MouthTightenerRight: float = 0.0
    MouthTightenerLeft: float = 0.0
    TongueOut: float = 0.0
    TongueUp: float = 0.0
    TongueDown: float = 0.0
    TongueRight: float = 0.0
    TongueLeft: float = 0.0
    TongueRoll: float = 0.0
    TongueBendDown: float = 0.0
    TongueCurlUp: float = 0.0
    TongueSquish: float = 0.0
    TongueFlat: float = 0.0
    TongueTwistRight: float = 0.0
    TongueTwistLeft: float = 0.0
    SoftPalateClose: float = 0.0
    ThroatSwallow: float = 0.0
    NeckFlexRight: float = 0.0
    NeckFlexLeft: float = 0.0

    @property
    def blob(self) -> tuple[int, ...]:
        return (
            clamp(0, int(self.EyeLookOutRight * 255), 255),
            clamp(0, int(self.EyeLookInRight * 255), 255),
            clamp(0, int(self.EyeLookUpRight * 255), 255),
            clamp(0, int(self.EyeLookDownRight * 255), 255),
            clamp(0, int(self.EyeLookOutLeft * 255), 255),
            clamp(0, int(self.EyeLookInLeft * 255), 255),
            clamp(0, int(self.EyeLookUpLeft * 255), 255),
            clamp(0, int(self.EyeLookDownLeft * 255), 255),
            clamp(0, int(self.EyeClosedRight * 255), 255),
            clamp(0, int(self.EyeClosedLeft * 255), 255),
            clamp(0, int(self.EyeDilationRight * 255), 255),
            clamp(0, int(self.EyeDilationLeft * 255), 255),
            clamp(0, int(self.EyeConstrictRight * 255), 255),
            clamp(0, int(self.EyeConstrictLeft * 255), 255),
            clamp(0, int(self.EyeSquintRight * 255), 255),
            clamp(0, int(self.EyeSquintLeft * 255), 255),
            clamp(0, int(self.EyeWideRight * 255), 255),
            clamp(0, int(self.EyeWideLeft * 255), 255),
            clamp(0, int(self.BrowPinchRight * 255), 255),
            clamp(0, int(self.BrowPinchLeft * 255), 255),
            clamp(0, int(self.BrowLowererRight * 255), 255),
            clamp(0, int(self.BrowLowererLeft * 255), 255),
            clamp(0, int(self.BrowInnerUpRight * 255), 255),
            clamp(0, int(self.BrowInnerUpLeft * 255), 255),
            clamp(0, int(self.BrowOuterUpRight * 255), 255),
            clamp(0, int(self.BrowOuterUpLeft * 255), 255),
            clamp(0, int(self.NasalDilationRight * 255), 255),
            clamp(0, int(self.NasalDilationLeft * 255), 255),
            clamp(0, int(self.NasalConstrictRight * 255), 255),
            clamp(0, int(self.NasalConstrictLeft * 255), 255),
            clamp(0, int(self.CheekSquintRight * 255), 255),
            clamp(0, int(self.CheekSquintLeft * 255), 255),
            clamp(0, int(self.CheekPuffRight * 255), 255),
            clamp(0, int(self.CheekPuffLeft * 255), 255),
            clamp(0, int(self.CheekSuckRight * 255), 255),
            clamp(0, int(self.CheekSuckLeft * 255), 255),
            clamp(0, int(self.JawOpen * 255), 255),
            clamp(0, int(self.JawRight * 255), 255),
            clamp(0, int(self.JawLeft * 255), 255),
            clamp(0, int(self.JawForward * 255), 255),
            clamp(0, int(self.JawBackward * 255), 255),
            clamp(0, int(self.JawClench * 255), 255),
            clamp(0, int(self.JawMandibleRaise * 255), 255),
            clamp(0, int(self.MouthClosed * 255), 255),
            clamp(0, int(self.LipSuckUpperRight * 255), 255),
            clamp(0, int(self.LipSuckUpperLeft * 255), 255),
            clamp(0, int(self.LipSuckLowerRight * 255), 255),
            clamp(0, int(self.LipSuckLowerLeft * 255), 255),
            clamp(0, int(self.LipSuckCornerRight * 255), 255),
            clamp(0, int(self.LipSuckCornerLeft * 255), 255),
            clamp(0, int(self.LipFunnelUpperRight * 255), 255),
            clamp(0, int(self.LipFunnelUpperLeft * 255), 255),
            clamp(0, int(self.LipFunnelLowerRight * 255), 255),
            clamp(0, int(self.LipFunnelLowerLeft * 255), 255),
            clamp(0, int(self.LipPuckerUpperRight * 255), 255),
            clamp(0, int(self.LipPuckerUpperLeft * 255), 255),
            clamp(0, int(self.LipPuckerLowerRight * 255), 255),
            clamp(0, int(self.LipPuckerLowerLeft * 255), 255),
            clamp(0, int(self.MouthUpperUpRight * 255), 255),
            clamp(0, int(self.MouthUpperUpLeft * 255), 255),
            clamp(0, int(self.MouthUpperDeepenRight * 255), 255),
            clamp(0, int(self.MouthUpperDeepenLeft * 255), 255),
            clamp(0, int(self.NoseSneerRight * 255), 255),
            clamp(0, int(self.NoseSneerLeft * 255), 255),
            clamp(0, int(self.MouthLowerDownRight * 255), 255),
            clamp(0, int(self.MouthLowerDownLeft * 255), 255),
            clamp(0, int(self.MouthUpperRight * 255), 255),
            clamp(0, int(self.MouthUpperLeft * 255), 255),
            clamp(0, int(self.MouthLowerRight * 255), 255),
            clamp(0, int(self.MouthLowerLeft * 255), 255),
            clamp(0, int(self.MouthCornerPullRight * 255), 255),
            clamp(0, int(self.MouthCornerPullLeft * 255), 255),
            clamp(0, int(self.MouthCornerSlantRight * 255), 255),
            clamp(0, int(self.MouthCornerSlantLeft * 255), 255),
            clamp(0, int(self.MouthFrownRight * 255), 255),
            clamp(0, int(self.MouthFrownLeft * 255), 255),
            clamp(0, int(self.MouthStretchRight * 255), 255),
            clamp(0, int(self.MouthStretchLeft * 255), 255),
            clamp(0, int(self.MouthDimpleRight * 255), 255),
            clamp(0, int(self.MouthDimpleLeft * 255), 255),
            clamp(0, int(self.MouthRaiserUpper * 255), 255),
            clamp(0, int(self.MouthRaiserLower * 255), 255),
            clamp(0, int(self.MouthPressRight * 255), 255),
            clamp(0, int(self.MouthPressLeft * 255), 255),
            clamp(0, int(self.MouthTightenerRight * 255), 255),
            clamp(0, int(self.MouthTightenerLeft * 255), 255),
            clamp(0, int(self.TongueOut * 255), 255),
            clamp(0, int(self.TongueUp * 255), 255),
            clamp(0, int(self.TongueDown * 255), 255),
            clamp(0, int(self.TongueRight * 255), 255),
            clamp(0, int(self.TongueLeft * 255), 255),
            clamp(0, int(self.TongueRoll * 255), 255),
            clamp(0, int(self.TongueBendDown * 255), 255),
            clamp(0, int(self.TongueCurlUp * 255), 255),
            clamp(0, int(self.TongueSquish * 255), 255),
            clamp(0, int(self.TongueFlat * 255), 255),
            clamp(0, int(self.TongueTwistRight * 255), 255),
            clamp(0, int(self.TongueTwistLeft * 255), 255),
            clamp(0, int(self.SoftPalateClose * 255), 255),
            clamp(0, int(self.ThroatSwallow * 255), 255),
            clamp(0, int(self.NeckFlexRight * 255), 255),
            clamp(0, int(self.NeckFlexLeft * 255), 255)
        )

    @property
    def bytestring(self) -> bytes:
        return bytes(self.blob)
