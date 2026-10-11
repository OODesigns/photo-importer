"""Limits that keep sustained copying from overheating the drives involved."""
from dataclasses import dataclass

from photo_importer.domain.throttle_level import ThrottleLevel

_MEGABYTE = 1024 * 1024


@dataclass(frozen=True)
class ThrottlePolicy:
    work_seconds: float
    rest_seconds: float
    max_bytes_per_second: int

    def __post_init__(self) -> None:
        if self.work_seconds < 0 or self.rest_seconds < 0 or self.max_bytes_per_second < 0:
            raise ValueError("ThrottlePolicy values must not be negative")

    @property
    def rests_between_work(self) -> bool:
        return self.work_seconds > 0 and self.rest_seconds > 0

    @property
    def caps_bandwidth(self) -> bool:
        return self.max_bytes_per_second > 0

    @staticmethod
    def for_level(level: ThrottleLevel) -> "ThrottlePolicy":
        return _POLICIES[level]


_POLICIES = {
    ThrottleLevel.OFF: ThrottlePolicy(work_seconds=0, rest_seconds=0, max_bytes_per_second=0),
    ThrottleLevel.NORMAL: ThrottlePolicy(work_seconds=300, rest_seconds=30, max_bytes_per_second=60 * _MEGABYTE),
    ThrottleLevel.GENTLE: ThrottlePolicy(work_seconds=60, rest_seconds=30, max_bytes_per_second=25 * _MEGABYTE),
}
