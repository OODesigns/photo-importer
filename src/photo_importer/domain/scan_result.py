"""Typed result of scanning a source folder, distinguishing completion from cancellation."""
from dataclasses import dataclass
from typing import List, Tuple

from photo_importer.domain.media_file import MediaFile


@dataclass(frozen=True)
class ScanResult:
    media_files: Tuple[MediaFile, ...]
    cancelled: bool

    @staticmethod
    def completed(media_files: List[MediaFile]) -> "ScanResult":
        return ScanResult(tuple(media_files), cancelled=False)

    @staticmethod
    def cancelled_with(media_files: List[MediaFile]) -> "ScanResult":
        return ScanResult(tuple(media_files), cancelled=True)
