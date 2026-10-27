from datetime import date

from atlas.services import ValidationError


def parse_iso_date(value: str | None) -> date | None:
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValidationError(f"invalid date {value!r}; use YYYY-MM-DD") from exc
