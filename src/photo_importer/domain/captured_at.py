"""Value object representing the moment a photo or video was captured."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CapturedAt:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is not None:
            object.__setattr__(self, "value", self.value.replace(tzinfo=None))

    @property
    def year(self) -> int:
        return self.value.year

    @property
    def month(self) -> int:
        return self.value.month

    @property
    def day(self) -> int:
        return self.value.day
