from datetime import datetime

from photo_importer.infrastructure.filesystem_gateway import RealFilesystemGateway


def test_iter_files_recurses_into_subfolders_and_skips_directories(tmp_path):
    (tmp_path / "nested" / "deeper").mkdir(parents=True)
    (tmp_path / "top.jpg").write_text("a")
    (tmp_path / "nested" / "mid.jpg").write_text("b")
    (tmp_path / "nested" / "deeper" / "bottom.jpg").write_text("c")

    gateway = RealFilesystemGateway()

    found = {path.name for path in gateway.iter_files(tmp_path)}

    assert found == {"top.jpg", "mid.jpg", "bottom.jpg"}


def test_exists_reflects_filesystem_state(tmp_path):
    gateway = RealFilesystemGateway()
    present = tmp_path / "present.jpg"
    present.write_text("x")

    assert gateway.exists(present) is True
    assert gateway.exists(tmp_path / "missing.jpg") is False


def test_modified_at_matches_stat_mtime(tmp_path):
    gateway = RealFilesystemGateway()
    path = tmp_path / "file.jpg"
    path.write_text("x")

    assert gateway.modified_at(path) == datetime.fromtimestamp(path.stat().st_mtime)


def test_make_parent_directories_creates_missing_nested_dirs(tmp_path):
    gateway = RealFilesystemGateway()
    target = tmp_path / "a" / "b" / "c" / "file.jpg"

    gateway.make_parent_directories(target)

    assert target.parent.is_dir()


def test_copy_file_duplicates_content(tmp_path):
    gateway = RealFilesystemGateway()
    source = tmp_path / "source.jpg"
    source.write_bytes(b"hello")
    destination = tmp_path / "dest" / "copy.jpg"
    gateway.make_parent_directories(destination)

    gateway.copy_file(source, destination)

    assert destination.read_bytes() == b"hello"
