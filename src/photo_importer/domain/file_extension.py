"""Value object representing a normalized file extension."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FileExtension:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower().lstrip(".")
        if not normalized:
            raise ValueError("FileExtension must not be empty")
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def of(raw: str) -> "FileExtension":
        return FileExtension(raw)
