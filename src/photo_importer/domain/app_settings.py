"""Value object for the user's configurable, persisted import settings."""
from dataclasses import dataclass
from pathlib import Path

from photo_importer.domain.destination_pattern import DestinationPattern

_DEFAULT_SOURCE_FOLDER = Path("/mnt/share home/Photos")
_DEFAULT_DESTINATION_FOLDER = Path("/mnt/photo")


@dataclass(frozen=True)
class AppSettings:
    source_folder: Path
    destination_folder: Path
    destination_pattern: DestinationPattern

    def __post_init__(self) -> None:
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
