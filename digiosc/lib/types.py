IP = str
Port = int
Seconds = float
URL = str

OSCReturnable = float | int | bool
Atomic = float | int | str | bool
Velocity = tuple[float, float, float]

UNFETCHED = object()
# !: Typing might hate this! It's a hack, but it allows for cleaner DX, ala:
# if avatar.get_parameter_value("Name"):
UNFETCHED.__setattr__("__bool__", lambda: False)

