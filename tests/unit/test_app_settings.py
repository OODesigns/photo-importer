from pathlib import Path

import pytest

from photo_importer.domain.app_settings import AppSettings
from photo_importer.domain.destination_pattern import DestinationPattern


def test_defaults_match_known_nas_convention():
    defaults = AppSettings.defaults()

    assert defaults.source_folder == Path("/mnt/share home/Photos")
    assert defaults.destination_folder == Path("/mnt/photo")
    assert defaults.destination_pattern.template == DestinationPattern.default().template


def test_rejects_blank_source_folder():
    with pytest.raises(ValueError):
        AppSettings(Path(""), Path("/mnt/photo"), DestinationPattern.default())


def test_rejects_blank_destination_folder():
    with pytest.raises(ValueError):
        AppSettings(Path("/mnt/share home/Photos"), Path(""), DestinationPattern.default())
