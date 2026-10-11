"""Boundary between the application core and the real filesystem."""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol


class FilesystemGateway(Protocol):
    def iter_files(self, root: Path) -> Iterable[Path]: ...
    def exists(self, path: Path) -> bool: ...
    def modified_at(self, path: Path) -> datetime: ...
    def make_parent_directories(self, path: Path) -> None: ...
    def copy_file(self, source: Path, destination: Path) -> None: ...


class RealFilesystemGateway:
    """FilesystemGateway implementation backed by the operating system."""

    def iter_files(self, root: Path) -> Iterable[Path]:
        # Lazy: yields as it walks, so callers can report progress/cancel without
        # waiting for the whole (possibly huge, possibly networked) tree to be listed.
        return (path for path in root.rglob("*") if path.is_file())

    def exists(self, path: Path) -> bool:
        return path.exists()

    def modified_at(self, path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime)

    def make_parent_directories(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def copy_file(self, source: Path, destination: Path) -> None:
        shutil.copy2(source, destination)
