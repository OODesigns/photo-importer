from pathlib import Path

import pytest

from photo_importer.domain.app_settings import AppSettings
from photo_importer.domain.destination_pattern import DestinationPattern
from photo_importer.domain.throttle_level import ThrottleLevel
from photo_importer.infrastructure.app_settings_store import AppSettingsStore


def test_load_returns_defaults_when_config_file_is_missing(tmp_path):
    store = AppSettingsStore(tmp_path / "missing" / "config.json")

    settings = store.load()

    assert settings == AppSettings.defaults()


def test_save_then_load_round_trips_settings(tmp_path):
    store = AppSettingsStore(tmp_path / "config.json")
    saved = AppSettings(
        source_folder=Path("/mnt/custom-source"),
        destination_folder=Path("/mnt/custom-dest"),
        destination_pattern=DestinationPattern("{category}/{year}/{filename}"),
    )

    store.save(saved)
    loaded = store.load()

    assert loaded == saved


def test_save_then_load_round_trips_throttle_level_and_batch_limit(tmp_path):
    store = AppSettingsStore(tmp_path / "config.json")
    saved = AppSettings(
        source_folder=Path("/a"),
        destination_folder=Path("/b"),
        destination_pattern=DestinationPattern.default(),
        throttle_level=ThrottleLevel.VERY_GENTLE,
        batch_limit=500,
    )

    store.save(saved)

    assert store.load() == saved


def test_app_settings_rejects_negative_batch_limit():
    with pytest.raises(ValueError):
        AppSettings(Path("/a"), Path("/b"), DestinationPattern.default(), batch_limit=-1)


def test_load_falls_back_to_defaults_on_corrupt_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("not valid json")
    store = AppSettingsStore(config_path)

    assert store.load() == AppSettings.defaults()


def test_load_falls_back_to_defaults_when_fields_are_missing(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"source_folder": "/only/one/field"}')
    store = AppSettingsStore(config_path)

    assert store.load() == AppSettings.defaults()


def test_load_falls_back_to_defaults_on_invalid_pattern(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"source_folder": "/a", "destination_folder": "/b", "destination_pattern": "../{filename}"}'
    )
    store = AppSettingsStore(config_path)

    assert store.load() == AppSettings.defaults()


def test_save_creates_parent_directories(tmp_path):
    config_path = tmp_path / "nested" / "dir" / "config.json"
    store = AppSettingsStore(config_path)

    store.save(AppSettings.defaults())

    assert config_path.exists()


def test_default_config_path_respects_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = AppSettingsStore.default_config_path()

    assert config_path == tmp_path / "photo-importer" / "config.json"
