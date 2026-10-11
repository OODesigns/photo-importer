"""Classification of media files, mirroring the folder convention under /mnt/photo."""
from enum import Enum

from photo_importer.domain.file_extension import FileExtension

_RAW_EXTENSIONS = frozenset({"cr2", "cr3", "nef", "arw", "dng", "raf", "orf", "rw2", "pef", "srw"})
_PHOTO_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "heic", "heif", "tif", "tiff", "bmp", "gif", "webp"})
_VIDEO_EXTENSIONS = frozenset({"mp4", "mov", "avi", "mkv", "m4v", "3gp"})


class FileCategory(Enum):
    RAW = "RAW"
    JPEG = "JPEG"
    VIDEO = "VIDEO"
    OTHER = "OTHER"

    @staticmethod
    def from_extension(extension: FileExtension) -> "FileCategory":
        if extension.value in _RAW_EXTENSIONS:
            return FileCategory.RAW
        if extension.value in _PHOTO_EXTENSIONS:
            return FileCategory.JPEG
        if extension.value in _VIDEO_EXTENSIONS:
            return FileCategory.VIDEO
        return FileCategory.OTHER

    @property
    def is_supported_media(self) -> bool:
        return self is not FileCategory.OTHER
