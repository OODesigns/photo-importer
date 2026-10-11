"""Discovers importable media files beneath a chosen source folder."""
from pathlib import Path
from typing import Callable, List, Optional

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.duty_cycle_throttle import DutyCycleThrottle
from photo_importer.domain.file_category import FileCategory
from photo_importer.domain.file_extension import FileExtension
from photo_importer.domain.media_file import MediaFile
from photo_importer.domain.scan_result import ScanResult
from photo_importer.infrastructure.exif_date_reader import ExifDateReader
from photo_importer.infrastructure.filesystem_gateway import FilesystemGateway

FileFoundCallback = Callable[[Path], None]


class SourceFolderScanner:
    def __init__(self, filesystem_gateway: FilesystemGateway, date_reader: ExifDateReader) -> None:
        self._filesystem_gateway = filesystem_gateway
        self._date_reader = date_reader

    def scan(
        self,
        source_folder: Path,
        on_file_found: Optional[FileFoundCallback] = None,
        cancellation_token: Optional[CancellationToken] = None,
        throttle: Optional[DutyCycleThrottle] = None,
    ) -> ScanResult:
        media_files: List[MediaFile] = []
        for path in self._filesystem_gateway.iter_files(source_folder):
            if throttle is not None:
                throttle.rest_if_due(cancellation_token)
            if cancellation_token is not None and cancellation_token.is_cancel_requested:
                return ScanResult.cancelled_with(media_files)
            category = FileCategory.from_extension(FileExtension.of(path.suffix))
            if not category.is_supported_media:
                continue
            if on_file_found is not None:
                on_file_found(path)
            captured_at = self._date_reader.captured_at_of(path, category)
            media_files.append(MediaFile.discovered(path, captured_at))
        return ScanResult.completed(media_files)

    @staticmethod
    def _is_supported_media(path: Path) -> bool:
        return FileCategory.from_extension(FileExtension.of(path.suffix)).is_supported_media
