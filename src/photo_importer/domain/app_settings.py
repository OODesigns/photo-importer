"""Value object for the user's configurable, persisted import settings."""
from dataclasses import dataclass
from pathlib import Path

from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.throttle_level import ThrottleLevel

_DEFAULT_SOURCE_FOLDER = Path("/mnt/share home/Photos")
_DEFAULT_DESTINATION_FOLDER = Path("/mnt/photo")


@dataclass(frozen=True)
class AppSettings:
    source_folder: Path
    destination_folder: Path
    destination_pattern: DestinationPattern
    throttle_level: ThrottleLevel = ThrottleLevel.GENTLE
    batch_limit: int = 0

    def __post_init__(self) -> None:
        if self.batch_limit < 0:
            raise ValueError("AppSettings batch limit must not be negative")
        if not self.source_folder.parts:
            raise ValueError("AppSettings requires a source folder")
        if not self.destination_folder.parts:
            raise ValueError("AppSettings requires a destination folder")

    @staticmethod
    def defaults() -> "AppSettings":
        return AppSettings(
            source_folder=_DEFAULT_SOURCE_FOLDER,
            destination_folder=_DEFAULT_DESTINATION_FOLDER,
            destination_pattern=DestinationPattern.default(),
        )
