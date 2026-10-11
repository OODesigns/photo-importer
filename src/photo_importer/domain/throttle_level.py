"""How hard an import is allowed to push the storage it reads from and writes to."""
from enum import Enum


class ThrottleLevel(Enum):
    OFF = "off"
    NORMAL = "normal"
    GENTLE = "gentle"
    VERY_GENTLE = "very_gentle"
