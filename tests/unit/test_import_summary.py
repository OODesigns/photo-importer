from datetime import datetime
from pathlib import Path

from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.import_entry_result import ImportEntryResult
from photo_importer.domain.import_plan_entry import ImportPlanEntry
from photo_importer.domain.import_summary import ImportSummary
from photo_importer.domain.media_file import MediaFile


def _entry():
    media_file = MediaFile.discovered(Path("/source/a.jpg"), CapturedAt(datetime(2026, 1, 1)))
    return ImportPlanEntry(media_file, Path("/dest/a.jpg"))


def test_summary_counts_each_outcome():
    entry = _entry()
    summary = ImportSummary.of(
        [
            ImportEntryResult.copied(entry),
            ImportEntryResult.copied(entry),
            ImportEntryResult.skipped_duplicate(entry),
            ImportEntryResult.failed(entry, "boom"),
        ]
    )

    assert summary.copied_count == 2
    assert summary.skipped_count == 1
    assert summary.failed_count == 1
    assert summary.total_count == 4


def test_summary_defaults_to_not_cancelled():
    assert ImportSummary.of([]).cancelled is False


def test_summary_can_be_marked_cancelled():
    assert ImportSummary.of([], cancelled=True).cancelled is True
