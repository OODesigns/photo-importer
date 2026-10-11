"""Boundary between the application core and the real filesystem."""
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Protocol

_CHUNK_BYTES = 1024 * 1024
_PARTIAL_SUFFIX = ".partial"


class FilesystemGateway(Protocol):
    def iter_files(self, root: Path) -> Iterable[Path]: ...
    def exists(self, path: Path) -> bool: ...
    def file_size(self, path: Path) -> int: ...
    def modified_at(self, path: Path) -> datetime: ...
    def make_parent_directories(self, path: Path) -> None: ...
    def copy_file(self, source: Path, destination: Path) -> None: ...


class RealFilesystemGateway:
    """FilesystemGateway implementation backed by the operating system."""

    def __init__(
        self,
        max_bytes_per_second: int = 0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._max_bytes_per_second = max_bytes_per_second
        self._clock = clock
        self._sleep = sleep

    def iter_files(self, root: Path) -> Iterable[Path]:
        # Lazy: yields as it walks, so callers can report progress/cancel without
        # waiting for the whole (possibly huge, possibly networked) tree to be listed.
        return (path for path in root.rglob("*") if path.is_file())

    def exists(self, path: Path) -> bool:
        return path.exists()

    def file_size(self, path: Path) -> int:
        return path.stat().st_size

    def modified_at(self, path: Path) -> datetime:
        return datetime.fromtimestamp(path.stat().st_mtime)

    def make_parent_directories(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def copy_file(self, source: Path, destination: Path) -> None:
        # Written under a temporary name so an interrupted copy never looks complete.
        partial = destination.with_name(destination.name + _PARTIAL_SUFFIX)
        try:
            self._copy_in_chunks(source, partial)
            os.replace(partial, destination)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        self._copy_timestamps(source, destination)

    def _copy_in_chunks(self, source: Path, target: Path) -> None:
        started_at = self._clock()
        copied_bytes = 0
        with source.open("rb") as reader, target.open("wb") as writer:
            while chunk := reader.read(_CHUNK_BYTES):
                writer.write(chunk)
                copied_bytes += len(chunk)
                self._sleep_to_stay_under_cap(copied_bytes, started_at)

    def _sleep_to_stay_under_cap(self, copied_bytes: int, started_at: float) -> None:
        if self._max_bytes_per_second <= 0:
            return
        allowed_elapsed = copied_bytes / self._max_bytes_per_second
        ahead_by = allowed_elapsed - (self._clock() - started_at)
        if ahead_by > 0:
            self._sleep(ahead_by)

    @staticmethod
    def _copy_timestamps(source: Path, destination: Path) -> None:
        stat = source.stat()
        os.utime(destination, ns=(stat.st_atime_ns, stat.st_mtime_ns))
