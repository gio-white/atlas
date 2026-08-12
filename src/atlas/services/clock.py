from datetime import date

from atlas.settings import load_settings


def resolve_today(as_of: date | None) -> date:
    if as_of is not None:
        return as_of
    return load_settings().today()
