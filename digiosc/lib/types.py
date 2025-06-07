from typing import Literal


IP = str
Port = int
Seconds = float
URL = str

OSCReturnable = float | int | bool
Atomic = float | int | str | bool
Velocity = tuple[float, float, float]

class UnfetchedType:
    def __bool__(self) -> Literal[False]:
        return False

UNFETCHED = UnfetchedType()

ParameterReturnValue = OSCReturnable | UnfetchedType
