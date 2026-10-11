from datetime import datetime
from pathlib import Path

import pytest

from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.file_category import FileCategory
from photo_importer.domain.media_file import MediaFile


def test_discovered_derives_extension_and_category():
    media_file = MediaFile.discovered(Path("/tmp/source/IMG_0001.CR3"), CapturedAt(datetime(2026, 6, 6)))

    assert media_file.extension.value == "cr3"
    assert media_file.category is FileCategory.RAW


def test_discovered_rejects_path_without_filename():
    with pytest.raises(ValueError):
        MediaFile.discovered(Path("/"), CapturedAt(datetime(2026, 6, 6)))
