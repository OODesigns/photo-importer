from datetime import datetime
from pathlib import Path

from photo_importer.application.import_planner import ImportPlanner
from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.media_file import MediaFile


def test_plan_for_computes_destination_under_root():
    media_file = MediaFile.discovered(Path("/source/IMG_0001.JPG"), CapturedAt(datetime(2026, 6, 6)))
    planner = ImportPlanner(Path("/mnt/photo"), DestinationPattern.default())

    [entry] = planner.plan_for([media_file])

    assert entry.media_file is media_file
    assert entry.destination_path == Path("/mnt/photo/2026/06-06/JPEG/IMG_0001.JPG")
