"""Reads the capture date of a media file, falling back to filesystem metadata."""
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, UnidentifiedImageError

from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.file_category import FileCategory
from photo_importer.infrastructure.filesystem_gateway import FilesystemGateway

_DATE_TIME_ORIGINAL_TAG = 36867
_DATE_TIME_TAG = 306
_EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
_EXIF_CAPABLE_CATEGORIES = frozenset({FileCategory.RAW, FileCategory.JPEG})


class ExifDateReader:
    def __init__(self, filesystem_gateway: FilesystemGateway) -> None:
        self._filesystem_gateway = filesystem_gateway

    def captured_at_of(self, path: Path, category: FileCategory) -> CapturedAt:
        if category in _EXIF_CAPABLE_CATEGORIES:
            exif_date = self._read_exif_date(path)
            if exif_date is not None:
                return CapturedAt(exif_date)
        return CapturedAt(self._filesystem_gateway.modified_at(path))

    def _read_exif_date(self, path: Path) -> Optional[datetime]:
        try:
            with Image.open(path) as image:
                exif = image.getexif()
                raw_value = exif.get(_DATE_TIME_ORIGINAL_TAG) or exif.get(_DATE_TIME_TAG)
        except (OSError, UnidentifiedImageError):
            return None
        if not raw_value:
            return None
        try:
            return datetime.strptime(raw_value, _EXIF_DATE_FORMAT)
        except ValueError:
            return None
