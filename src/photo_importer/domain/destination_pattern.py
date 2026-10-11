"""Configurable, user-editable naming scheme for where imported files land on the NAS."""
from dataclasses import dataclass
from pathlib import Path

from photo_importer.domain.media_file import MediaFile

_PREVIEW_TOKENS = {"year": 2000, "month": "01", "day": "01", "category": "RAW", "filename": "example.jpg"}


@dataclass(frozen=True)
class DestinationPattern:
    template: str

    def __post_init__(self) -> None:
        trimmed = self.template.strip()
        if not trimmed:
            raise ValueError("DestinationPattern must not be empty")
        try:
            rendered_preview = trimmed.format(**_PREVIEW_TOKENS)
        except (KeyError, IndexError, ValueError) as error:
            raise ValueError(f"Invalid destination pattern '{trimmed}': {error}") from error
        if not self._is_contained(Path(rendered_preview)):
            raise ValueError(f"Destination pattern '{trimmed}' must not escape the destination folder")
        object.__setattr__(self, "template", trimmed)

    def render(self, media_file: MediaFile) -> Path:
        relative = Path(
            self.template.format(
                year=media_file.captured_at.year,
                month=f"{media_file.captured_at.month:02d}",
                day=f"{media_file.captured_at.day:02d}",
                category=media_file.category.value,
                filename=media_file.source_path.name,
            )
        )
        if not self._is_contained(relative):
            raise ValueError(f"Rendered destination '{relative}' must not escape the destination folder")
        return relative

    @staticmethod
    def _is_contained(relative_path: Path) -> bool:
        return not relative_path.is_absolute() and ".." not in relative_path.parts

    def preview(self) -> str:
        return self.template.format(**_PREVIEW_TOKENS)

    @staticmethod
    def default() -> "DestinationPattern":
        # Matches the existing /mnt/photo convention: <year>/<month>-<day>/<category>/<filename>
        return DestinationPattern("{year}/{month}-{day}/{category}/{filename}")
