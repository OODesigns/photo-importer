import pytest

from photo_importer.domain.file_extension import FileExtension


def test_normalizes_case_and_strips_leading_dot():
    assert FileExtension.of(".CR3").value == "cr3"


def test_rejects_empty_extension():
    with pytest.raises(ValueError):
        FileExtension.of("")
