from datetime import datetime
from pathlib import Path

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.source_folder_scanner import SourceFolderScanner
from photo_importer.domain.captured_at import CapturedAt
from photo_importer.domain.file_category import FileCategory


class _FakeFilesystemGateway:
    def __init__(self, files):
        self._files = files

    def iter_files(self, root):
        return iter(self._files)


class _FakeDateReader:
    def __init__(self, captured_at):
        self._captured_at = captured_at
        self.categories_seen = []

    def captured_at_of(self, path, category):
        self.categories_seen.append(category)
        return self._captured_at


def _scanner(files):
    return SourceFolderScanner(_FakeFilesystemGateway(files), _FakeDateReader(CapturedAt(datetime(2026, 6, 6))))


def test_scan_passes_the_derived_category_to_the_date_reader():
    files = [Path("/source/IMG_0001.CR3"), Path("/source/IMG_0002.jpg")]
    date_reader = _FakeDateReader(CapturedAt(datetime(2026, 6, 6)))
    scanner = SourceFolderScanner(_FakeFilesystemGateway(files), date_reader)

    scanner.scan(Path("/source"))

    assert date_reader.categories_seen == [FileCategory.RAW, FileCategory.JPEG]


def test_scan_filters_unsupported_files_and_builds_media_files():
    files = [Path("/source/IMG_0001.CR3"), Path("/source/notes.txt"), Path("/source/IMG_0002.jpg")]

    result = _scanner(files).scan(Path("/source"))

    assert not result.cancelled
    assert [media_file.source_path for media_file in result.media_files] == [
        Path("/source/IMG_0001.CR3"),
        Path("/source/IMG_0002.jpg"),
    ]


def test_scan_invokes_on_file_found_only_for_supported_media():
    files = [Path("/source/IMG_0001.CR3"), Path("/source/notes.txt"), Path("/source/IMG_0002.jpg")]
    found = []

    _scanner(files).scan(Path("/source"), on_file_found=found.append)

    assert found == [Path("/source/IMG_0001.CR3"), Path("/source/IMG_0002.jpg")]


def test_scan_stops_early_when_cancellation_requested():
    files = [Path(f"/source/IMG_{i:04d}.jpg") for i in range(5)]
    token = CancellationToken()

    def cancel_after_first(_path):
        token.request_cancel()

    result = _scanner(files).scan(Path("/source"), on_file_found=cancel_after_first, cancellation_token=token)

    assert result.cancelled
    assert len(result.media_files) == 1


def test_scan_rests_via_throttle_before_each_file():
    files = [Path(f"/source/IMG_{i:04d}.jpg") for i in range(3)]

    class _CountingThrottle:
        calls = 0

        def rest_if_due(self, _token=None):
            self.calls += 1

    throttle = _CountingThrottle()

    _scanner(files).scan(Path("/source"), throttle=throttle)

    assert throttle.calls == 3
