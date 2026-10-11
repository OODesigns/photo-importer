from datetime import datetime

from PIL import Image

from photo_importer.domain.file_category import FileCategory
from photo_importer.infrastructure.exif_date_reader import ExifDateReader
from photo_importer.infrastructure.filesystem_gateway import RealFilesystemGateway


def _write_jpeg(path, captured_at=None):
    image = Image.new("RGB", (2, 2), color="red")
    if captured_at is not None:
        exif = image.getexif()
        exif[36867] = captured_at.strftime("%Y:%m:%d %H:%M:%S")
        image.save(path, format="JPEG", exif=exif)
    else:
        image.save(path, format="JPEG")


def test_reads_date_time_original_from_exif(tmp_path):
    photo_path = tmp_path / "with_exif.jpg"
    _write_jpeg(photo_path, datetime(2026, 6, 6, 10, 30, 0))

    reader = ExifDateReader(RealFilesystemGateway())
    captured_at = reader.captured_at_of(photo_path, FileCategory.JPEG)

    assert (captured_at.year, captured_at.month, captured_at.day) == (2026, 6, 6)


def test_falls_back_to_modified_time_when_no_exif(tmp_path):
    photo_path = tmp_path / "without_exif.jpg"
    _write_jpeg(photo_path)

    reader = ExifDateReader(RealFilesystemGateway())
    captured_at = reader.captured_at_of(photo_path, FileCategory.JPEG)

    expected = datetime.fromtimestamp(photo_path.stat().st_mtime)
    assert (captured_at.year, captured_at.month, captured_at.day) == (expected.year, expected.month, expected.day)


def test_falls_back_to_modified_time_for_non_image_file(tmp_path):
    raw_like_path = tmp_path / "clip.cr3"
    raw_like_path.write_bytes(b"not a real raw file")

    reader = ExifDateReader(RealFilesystemGateway())
    captured_at = reader.captured_at_of(raw_like_path, FileCategory.RAW)

    expected = datetime.fromtimestamp(raw_like_path.stat().st_mtime)
    assert (captured_at.year, captured_at.month, captured_at.day) == (expected.year, expected.month, expected.day)


def test_skips_exif_read_entirely_for_video_category(tmp_path):
    # Even though this file has a readable EXIF date, VIDEO must not attempt to read it.
    photo_path = tmp_path / "clip.mp4"
    _write_jpeg(photo_path, datetime(2020, 1, 1, 0, 0, 0))

    reader = ExifDateReader(RealFilesystemGateway())
    captured_at = reader.captured_at_of(photo_path, FileCategory.VIDEO)

    expected = datetime.fromtimestamp(photo_path.stat().st_mtime)
    assert (captured_at.year, captured_at.month, captured_at.day) == (expected.year, expected.month, expected.day)


def test_skips_exif_read_entirely_for_other_category(tmp_path):
    photo_path = tmp_path / "notes.txt"
    _write_jpeg(photo_path, datetime(2020, 1, 1, 0, 0, 0))

    reader = ExifDateReader(RealFilesystemGateway())
    captured_at = reader.captured_at_of(photo_path, FileCategory.OTHER)

    expected = datetime.fromtimestamp(photo_path.stat().st_mtime)
    assert (captured_at.year, captured_at.month, captured_at.day) == (expected.year, expected.month, expected.day)
