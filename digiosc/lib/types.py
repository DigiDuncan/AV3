from typing import Literal


IP = str
Port = int
Seconds = float
URL = str

OSCReturnable = float | int | bool
Atomic = float | int | str | bool

float1 = tuple[float]
float2 = tuple[float, float]
Velocity = Rotation = Position = float3 = tuple[float, float, float]
float4 = tuple[float, float, float, float]
float6 = tuple[float, float, float, float, float, float]
floats = tuple[float, ...]

class UnfetchedType:
    def __bool__(self) -> Literal[False]:
        return False

UNFETCHED = UnfetchedType()

ParameterReturnValue = OSCReturnable | UnfetchedType
