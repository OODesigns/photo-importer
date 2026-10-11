"""Builds a concrete import plan from discovered media files, a pattern, and a destination root."""
from pathlib import Path
from typing import List

from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.import_plan_entry import ImportPlanEntry
from photo_importer.domain.media_file import MediaFile


class ImportPlanner:
    def __init__(self, destination_root: Path, destination_pattern: DestinationPattern) -> None:
        self._destination_root = destination_root
        self._destination_pattern = destination_pattern

    def plan_for(self, media_files: List[MediaFile]) -> List[ImportPlanEntry]:
        return [
            ImportPlanEntry(media_file, self._destination_root / self._destination_pattern.render(media_file))
            for media_file in media_files
        ]
