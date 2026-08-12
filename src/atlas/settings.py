import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DB_ENV_VAR = "ATLAS_DB"
TZ_ENV_VAR = "ATLAS_TZ"
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "atlas" / "atlas.db"


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    db_path: Path
    timezone: tzinfo

    def today(self) -> date:
        return datetime.now(self.timezone).date()


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    return Settings(
        db_path=_resolve_db_path(source.get(DB_ENV_VAR)),
        timezone=_resolve_timezone(source.get(TZ_ENV_VAR)),
    )


def _resolve_db_path(raw: str | None) -> Path:
    if raw is None or not raw.strip():
        return DEFAULT_DB_PATH
    return Path(raw).expanduser()


def _resolve_timezone(raw: str | None) -> tzinfo:
    if raw is None or not raw.strip():
        return _system_timezone()
    try:
        return ZoneInfo(raw.strip())
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise SettingsError(f"{TZ_ENV_VAR}={raw!r} is not a known IANA time zone") from exc


def _system_timezone() -> tzinfo:
    local = datetime.now().astimezone().tzinfo
    if local is None:
        raise SettingsError("the system time zone could not be determined; set ATLAS_TZ")
    return local
