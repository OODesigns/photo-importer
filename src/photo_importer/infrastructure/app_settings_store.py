"""Loads and saves AppSettings as JSON under the user's XDG config directory."""
import json
import os
from pathlib import Path

from photo_importer.domain.app_settings import AppSettings
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.throttle_level import ThrottleLevel

_CONFIG_FILE_NAME = "config.json"


class AppSettingsStore:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> AppSettings:
        try:
            raw = json.loads(self._config_path.read_text())
        except (OSError, json.JSONDecodeError):
            return AppSettings.defaults()
        try:
            return AppSettings(
                source_folder=Path(raw["source_folder"]),
                destination_folder=Path(raw["destination_folder"]),
                destination_pattern=DestinationPattern(raw["destination_pattern"]),
                throttle_level=ThrottleLevel(raw.get("throttle_level", ThrottleLevel.GENTLE.value)),
            )
        except (KeyError, TypeError, ValueError):
            return AppSettings.defaults()

    def save(self, settings: AppSettings) -> None:
        payload = {
            "source_folder": str(settings.source_folder),
            "destination_folder": str(settings.destination_folder),
            "destination_pattern": settings.destination_pattern.template,
            "throttle_level": settings.throttle_level.value,
        }
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(json.dumps(payload, indent=2) + "\n")

    @staticmethod
    def default_config_path() -> Path:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        base = Path(config_home) if config_home else Path.home() / ".config"
        return base / "photo-importer" / _CONFIG_FILE_NAME
