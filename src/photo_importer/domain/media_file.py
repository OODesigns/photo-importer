"""Value object representing a single discovered media file awaiting import."""
from dataclasses import dataclass
from pathlib import Path

from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.file_category import FileCategory
from photo_importer.domain.file_extension import FileExtension


@dataclass(frozen=True)
class MediaFile:
    source_path: Path
    extension: FileExtension
    category: FileCategory
    captured_at: CapturedAt

    @staticmethod
    def discovered(source_path: Path, captured_at: CapturedAt) -> "MediaFile":
        if not source_path.name:
            raise ValueError("MediaFile requires a source path with a file name")
        extension = FileExtension.of(source_path.suffix)
        category = FileCategory.from_extension(extension)
        return MediaFile(source_path, extension, category, captured_at)
