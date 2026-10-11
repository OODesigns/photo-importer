from datetime import datetime
from pathlib import Path

import pytest

from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.media_file import MediaFile


def _media_file(name="IMG_0001.CR3", captured=datetime(2026, 6, 6)):
    return MediaFile.discovered(Path(f"/source/{name}"), CapturedAt(captured))


def test_default_pattern_matches_existing_nas_convention():
    rendered = DestinationPattern.default().render(_media_file())
    assert rendered == Path("2026/06-06/RAW/IMG_0001.CR3")


def test_render_zero_pads_month_and_day():
    rendered = DestinationPattern.default().render(_media_file(captured=datetime(2026, 1, 2)))
    assert rendered == Path("2026/01-02/RAW/IMG_0001.CR3")


def test_rejects_empty_template():
    with pytest.raises(ValueError):
        DestinationPattern("   ")


def test_rejects_template_with_unknown_token():
    with pytest.raises(ValueError):
        DestinationPattern("{unknown}/{filename}")


def test_rejects_template_that_escapes_destination_root():
    with pytest.raises(ValueError):
        DestinationPattern("../../{filename}")


def test_rejects_absolute_template():
    with pytest.raises(ValueError):
        DestinationPattern("/etc/{filename}")


def test_preview_renders_example_values():
    assert DestinationPattern.default().preview() == "2000/01-01/RAW/example.jpg"


def test_source_path_traversal_components_do_not_leak_into_rendered_filename():
    # Path.name always strips any ".." / directory components, so even a
    # crafted source path can only ever contribute a single safe filename part.
    media_file = _media_file(name="evil.jpg")
    media_file = MediaFile.discovered(Path("/source/../../evil.jpg"), media_file.captured_at)

    rendered = DestinationPattern.default().render(media_file)

    assert rendered.name == "evil.jpg"
    assert ".." not in rendered.parts
