import os

import pytest

from photo_importer.infrastructure.filesystem_gateway import RealFilesystemGateway


def test_copy_leaves_no_partial_file_and_preserves_mtime(tmp_path):
    source = tmp_path / "source.jpg"
    source.write_bytes(b"hello")
    os.utime(source, (1_000_000, 1_000_000))
    destination = tmp_path / "copy.jpg"

    RealFilesystemGateway().copy_file(source, destination)

    assert destination.read_bytes() == b"hello"
    assert destination.stat().st_mtime == 1_000_000
    assert not (tmp_path / "copy.jpg.partial").exists()


def test_failed_copy_removes_partial_and_leaves_no_destination(tmp_path):
    destination = tmp_path / "copy.jpg"

    with pytest.raises(OSError):
        RealFilesystemGateway().copy_file(tmp_path / "missing.jpg", destination)

    assert not destination.exists()
    assert not (tmp_path / "copy.jpg.partial").exists()


def test_file_size_reports_bytes(tmp_path):
    path = tmp_path / "a.bin"
    path.write_bytes(b"12345")

    assert RealFilesystemGateway().file_size(path) == 5


def test_copy_sleeps_to_stay_under_bandwidth_cap(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"x" * (2 * 1024 * 1024))
    sleeps = []
    gateway = RealFilesystemGateway(
        max_bytes_per_second=1024 * 1024,
        clock=lambda: 0.0,
        sleep=sleeps.append,
    )

    gateway.copy_file(source, tmp_path / "dest.bin")

    assert sleeps == [1.0, 2.0]
