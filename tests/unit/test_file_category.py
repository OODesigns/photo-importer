import pytest

from photo_importer.domain.file_category import FileCategory
from photo_importer.domain.file_extension import FileExtension


@pytest.mark.parametrize(
    "extension, expected_category",
    [
        ("cr3", FileCategory.RAW),
        ("CR2", FileCategory.RAW),
        ("nef", FileCategory.RAW),
        ("jpg", FileCategory.JPEG),
        ("jpeg", FileCategory.JPEG),
        ("png", FileCategory.JPEG),
        ("mp4", FileCategory.VIDEO),
        ("mov", FileCategory.VIDEO),
        ("txt", FileCategory.OTHER),
    ],
)
def test_maps_extension_to_category(extension, expected_category):
    assert FileCategory.from_extension(FileExtension.of(extension)) is expected_category


def test_other_category_is_not_supported_media():
    assert FileCategory.OTHER.is_supported_media is False


def test_raw_category_is_supported_media():
    assert FileCategory.RAW.is_supported_media is True
