from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from atlas.settings import DEFAULT_DB_PATH, SettingsError, load_settings


def test_defaults_when_env_is_empty():
    settings = load_settings({})

    assert settings.db_path == DEFAULT_DB_PATH
    assert settings.timezone is not None


def test_reads_both_variables():
    settings = load_settings({"ATLAS_DB": "/tmp/atlas-test.db", "ATLAS_TZ": "Europe/Berlin"})

    assert settings.db_path == Path("/tmp/atlas-test.db")
    assert settings.timezone == ZoneInfo("Europe/Berlin")


def test_db_path_expands_user():
    settings = load_settings({"ATLAS_DB": "~/atlas.db"})

    assert settings.db_path == Path.home() / "atlas.db"


def test_blank_values_fall_back_to_defaults():
    settings = load_settings({"ATLAS_DB": "  ", "ATLAS_TZ": ""})

    assert settings.db_path == DEFAULT_DB_PATH
    assert settings.timezone is not None


def test_unknown_timezone_is_rejected():
    with pytest.raises(SettingsError, match="Mars/Olympus"):
        load_settings({"ATLAS_TZ": "Mars/Olympus"})


def test_today_uses_the_configured_timezone():
    kiritimati = load_settings({"ATLAS_TZ": "Pacific/Kiritimati"}).today()
    baker = load_settings({"ATLAS_TZ": "Pacific/Midway"}).today()

    assert kiritimati >= baker
