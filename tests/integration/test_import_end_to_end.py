"""End-to-end test of scan -> plan -> execute against a real (temporary) filesystem."""
from datetime import datetime
from pathlib import Path

from PIL import Image

from photo_importer.application.cancellation_token import CancellationToken
from photo_importer.application.import_executor import ImportExecutor
from photo_importer.application.import_planner import ImportPlanner
from photo_importer.application.source_folder_scanner import SourceFolderScanner
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.infrastructure.exif_date_reader import ExifDateReader
from photo_importer.infrastructure.filesystem_gateway import RealFilesystemGateway


def _write_jpeg_with_capture_date(path: Path, captured_at: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (2, 2), color="blue")
    exif = image.getexif()
    exif[36867] = captured_at.strftime("%Y:%m:%d %H:%M:%S")
    image.save(path, exif=exif)


def _run_pipeline(source_folder: Path, destination_folder: Path, pattern: DestinationPattern):
    filesystem_gateway = RealFilesystemGateway()
    scanner = SourceFolderScanner(filesystem_gateway, ExifDateReader(filesystem_gateway))
    scan_result = scanner.scan(source_folder)
    plan_entries = ImportPlanner(destination_folder, pattern).plan_for(list(scan_result.media_files))
    return ImportExecutor(filesystem_gateway).execute(plan_entries)


def test_imports_nested_photos_into_dated_category_folders(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    _write_jpeg_with_capture_date(source_folder / "camera" / "IMG_0001.jpg", datetime(2026, 6, 6, 9, 0, 0))
    (source_folder / "camera" / "ignored.txt").write_text("not a photo")

    summary = _run_pipeline(source_folder, destination_folder, DestinationPattern.default())

    expected_path = destination_folder / "2026" / "06-06" / "JPEG" / "IMG_0001.jpg"
    assert expected_path.exists()
    assert summary.copied_count == 1
    assert summary.skipped_count == 0
    assert summary.failed_count == 0


def test_running_twice_skips_existing_files_without_overwriting(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    photo_path = source_folder / "IMG_0002.jpg"
    _write_jpeg_with_capture_date(photo_path, datetime(2026, 1, 2, 12, 0, 0))

    _run_pipeline(source_folder, destination_folder, DestinationPattern.default())
    destination_path = destination_folder / "2026" / "01-02" / "JPEG" / "IMG_0002.jpg"
    original_bytes = destination_path.read_bytes()

    second_summary = _run_pipeline(source_folder, destination_folder, DestinationPattern.default())

    assert second_summary.copied_count == 0
    assert second_summary.skipped_count == 1
    assert destination_path.read_bytes() == original_bytes


def test_honors_custom_destination_pattern(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    _write_jpeg_with_capture_date(source_folder / "IMG_0003.jpg", datetime(2026, 3, 4, 8, 0, 0))

    custom_pattern = DestinationPattern("{category}/{year}/{filename}")
    summary = _run_pipeline(source_folder, destination_folder, custom_pattern)

    assert (destination_folder / "JPEG" / "2026" / "IMG_0003.jpg").exists()
    assert summary.copied_count == 1


def test_cancelling_during_scan_stops_before_any_file_is_copied(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    for index in range(3):
        _write_jpeg_with_capture_date(source_folder / f"IMG_{index}.jpg", datetime(2026, 6, 6, 9, 0, 0))

    filesystem_gateway = RealFilesystemGateway()
    scanner = SourceFolderScanner(filesystem_gateway, ExifDateReader(filesystem_gateway))
    token = CancellationToken()

    scan_result = scanner.scan(
        source_folder,
        on_file_found=lambda _path: token.request_cancel(),
        cancellation_token=token,
    )

    assert scan_result.cancelled is True
    assert len(scan_result.media_files) == 1
    assert not destination_folder.exists()


def test_cancelling_during_execution_stops_copying_remaining_files(tmp_path):
    source_folder = tmp_path / "source"
    destination_folder = tmp_path / "destination"
    for index in range(3):
        _write_jpeg_with_capture_date(source_folder / f"IMG_{index}.jpg", datetime(2026, 6, 6, 9, 0, 0))

    filesystem_gateway = RealFilesystemGateway()
    scanner = SourceFolderScanner(filesystem_gateway, ExifDateReader(filesystem_gateway))
    scan_result = scanner.scan(source_folder)
    plan_entries = ImportPlanner(destination_folder, DestinationPattern.default()).plan_for(
        list(scan_result.media_files)
    )
    token = CancellationToken()

    def cancel_after_first(_result):
        token.request_cancel()

    summary = ImportExecutor(filesystem_gateway).execute(
        plan_entries, on_progress=cancel_after_first, cancellation_token=token
    )

    assert summary.cancelled is True
    assert summary.copied_count == 1
