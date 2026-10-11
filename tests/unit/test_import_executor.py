from datetime import datetime
from pathlib import Path

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.import_executor import ImportExecutor
from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.import_outcome import ImportOutcome
from photo_importer.domain.import_plan_entry import ImportPlanEntry
from photo_importer.domain.media_file import MediaFile


class _FakeFilesystemGateway:
    def __init__(self, existing_paths=(), raise_on_copy=False, sizes=None):
        self._existing_paths = set(existing_paths)
        self._raise_on_copy = raise_on_copy
        self._sizes = sizes or {}
        self.copied = []
        self.created_parents_for = []

    def exists(self, path):
        return path in self._existing_paths

    def file_size(self, path):
        return self._sizes.get(path, 100)

    def make_parent_directories(self, path):
        self.created_parents_for.append(path)

    def copy_file(self, source, destination):
        if self._raise_on_copy:
            raise OSError("disk full")
        self.copied.append((source, destination))


def _entry(destination=Path("/dest/a.jpg")):
    media_file = MediaFile.discovered(Path("/source/a.jpg"), CapturedAt(datetime(2026, 1, 1)))
    return ImportPlanEntry(media_file, destination)


def test_copies_file_that_does_not_exist_yet():
    gateway = _FakeFilesystemGateway()
    executor = ImportExecutor(gateway)
    entry = _entry()

    [result] = executor.execute([entry]).results

    assert result.outcome is ImportOutcome.COPIED
    assert gateway.copied == [(entry.media_file.source_path, entry.destination_path)]
    assert gateway.created_parents_for == [entry.destination_path]


def test_skips_file_that_already_exists_without_copying():
    entry = _entry()
    gateway = _FakeFilesystemGateway(existing_paths={entry.destination_path})
    executor = ImportExecutor(gateway)

    [result] = executor.execute([entry]).results

    assert result.outcome is ImportOutcome.SKIPPED_DUPLICATE
    assert gateway.copied == []


def test_recopies_existing_file_whose_size_differs_from_source():
    entry = _entry()
    gateway = _FakeFilesystemGateway(
        existing_paths={entry.destination_path},
        sizes={entry.destination_path: 10},
    )
    executor = ImportExecutor(gateway)

    [result] = executor.execute([entry]).results

    assert result.outcome is ImportOutcome.COPIED
    assert len(gateway.copied) == 1


def test_stops_after_max_copies_and_flags_batch_limit():
    gateway = _FakeFilesystemGateway()
    executor = ImportExecutor(gateway)
    entries = [_entry(Path(f"/dest/{i}.jpg")) for i in range(5)]

    summary = executor.execute(entries, max_copies=2)

    assert summary.batch_limit_reached is True
    assert summary.cancelled is False
    assert len(gateway.copied) == 2


def test_skipped_files_do_not_count_toward_max_copies():
    skipped = _entry(Path("/dest/skip.jpg"))
    fresh = [_entry(Path(f"/dest/{i}.jpg")) for i in range(2)]
    gateway = _FakeFilesystemGateway(existing_paths={skipped.destination_path})
    executor = ImportExecutor(gateway)

    summary = executor.execute([skipped, *fresh], max_copies=2)

    assert summary.skipped_count == 1
    assert summary.copied_count == 2
    assert summary.batch_limit_reached is False


def test_records_failure_when_copy_raises_os_error():
    gateway = _FakeFilesystemGateway(raise_on_copy=True)
    executor = ImportExecutor(gateway)
    entry = _entry()

    [result] = executor.execute([entry]).results

    assert result.outcome is ImportOutcome.FAILED
    assert "disk full" in result.error_message


def test_invokes_progress_callback_per_entry():
    gateway = _FakeFilesystemGateway()
    executor = ImportExecutor(gateway)
    entry = _entry()
    observed = []

    executor.execute([entry], on_progress=observed.append)

    assert len(observed) == 1
    assert observed[0].outcome is ImportOutcome.COPIED


def test_stops_and_marks_cancelled_when_cancellation_requested_before_next_entry():
    gateway = _FakeFilesystemGateway()
    executor = ImportExecutor(gateway)
    entries = [_entry(Path(f"/dest/{i}.jpg")) for i in range(3)]
    token = CancellationToken()

    def cancel_after_first(_result):
        token.request_cancel()

    summary = executor.execute(entries, on_progress=cancel_after_first, cancellation_token=token)

    assert summary.cancelled is True
    assert summary.total_count == 1
    assert len(gateway.copied) == 1
