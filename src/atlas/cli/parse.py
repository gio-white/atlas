import re
from datetime import UTC, date, datetime

from atlas.domain import Comparator, Measure
from atlas.services import ValidationError

_SLUG_CHUNK = re.compile(r"[^a-z0-9]+")
_WEEKDAYS = {
    "mon": 1,
    "monday": 1,
    "tue": 2,
    "tues": 2,
    "tuesday": 2,
    "wed": 3,
    "wednesday": 3,
    "thu": 4,
    "thur": 4,
    "thurs": 4,
    "thursday": 4,
    "fri": 5,
    "friday": 5,
    "sat": 6,
    "saturday": 6,
    "sun": 7,
    "sunday": 7,
}
_TRUE = {"true", "yes", "y"}
_FALSE = {"false", "no", "n"}


def parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"invalid datetime {value!r}; use ISO-8601") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_iso_date(value: str | None) -> date | None:
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValidationError(f"invalid date {value!r}; use YYYY-MM-DD") from exc


def require_iso_date(value: str) -> date:
    parsed = parse_iso_date(value)
    if parsed is None:
        raise ValidationError(f"invalid date {value!r}; use YYYY-MM-DD")
    return parsed


def parse_log_value(raw: str | None) -> float | bool | str | None:
    if raw is None:
        return None
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    try:
        return float(raw)
    except ValueError:
        return raw


def slugify(text: str) -> str:
    compact = _SLUG_CHUNK.sub("-", text.strip().lower()).strip("-")
    if not compact:
        raise ValidationError(f"cannot derive a slug from {text!r}")
    return compact


def parse_weekdays(raw: str | None) -> list[int] | None:
    if raw is None or not raw.strip():
        return None
    days: list[int] = []
    for part in raw.split(","):
        token = part.strip().lower()
        if not token:
            continue
        if token.isdigit():
            days.append(int(token))
            continue
        if token not in _WEEKDAYS:
            raise ValidationError(f"invalid weekday {part!r}")
        days.append(_WEEKDAYS[token])
    if not days:
        raise ValidationError("weekdays must not be empty")
    return days


def comparator_and_target(
    at_least: float | None,
    at_most: float | None,
    exactly: float | None,
) -> tuple[Comparator, float]:
    present = [
        (comparator, value)
        for comparator, value in (
            (Comparator.AT_LEAST, at_least),
            (Comparator.AT_MOST, at_most),
            (Comparator.EXACTLY, exactly),
        )
        if value is not None
    ]
    if len(present) != 1:
        raise ValidationError("provide exactly one of --at-least, --at-most, --exactly")
    return present[0]


def comparator_from_flags(
    at_least: bool,
    at_most: bool,
    exactly: bool,
    *,
    default: Comparator | None = Comparator.AT_LEAST,
) -> Comparator | None:
    present = [
        comparator
        for comparator, flag in (
            (Comparator.AT_LEAST, at_least),
            (Comparator.AT_MOST, at_most),
            (Comparator.EXACTLY, exactly),
        )
        if flag
    ]
    if len(present) > 1:
        raise ValidationError("provide at most one of --at-least, --at-most, --exactly")
    if present:
        return present[0]
    return default


def measure_from_flag(cumulative: bool) -> Measure:
    if cumulative:
        return Measure.CUMULATIVE_SINCE_START
    return Measure.LATEST_VALUE
