"""Pairing of a discovered media file with its computed destination path."""
from dataclasses import dataclass
from pathlib import Path

from photo_importer.domain.media_file import MediaFile


@dataclass(frozen=True)
class ImportPlanEntry:
    media_file: MediaFile
    destination_path: Path
