from datetime import UTC, date, datetime

from sqlmodel import Session, select

from atlas.db.models import Entry, ScreenApp, ScreenSession
from atlas.domain import Source, ValueType
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import metric_by_id, require_active_metric, require_entry
from atlas.services.slugs import normalize_slug

_UNSET = object()


def log_entry(
    session: Session,
    metric_slug: str,
    value: float | bool | str | None = None,
    *,
    occurred_on: date | None = None,
    occurred_at: datetime | None = None,
    note: str | None = None,
    source: Source = Source.CLI,
    link_screen: bool = True,
) -> Entry:
    metric = require_active_metric(session, normalize_slug(metric_slug))
    value_num, value_bool, value_text = split_value(ValueType(metric.value_type), value)
    entry = Entry(
        metric_id=metric.id,
        occurred_on=_require_date(occurred_on if occurred_on is not None else resolve_today(None)),
        occurred_at=_as_utc(occurred_at),
        value_num=value_num,
        value_bool=value_bool,
        value_text=value_text,
        note=note,
        source=source,
    )
    session.add(entry)
    session.flush()
    if link_screen:
        _link_screen_session(session, entry)
    session.commit()
    session.refresh(entry)
    return entry


def amend_entry(
    session: Session,
    entry_id: int,
    *,
    value: float | bool | str | None | object = _UNSET,
    occurred_on: date | None | object = _UNSET,
    occurred_at: datetime | None | object = _UNSET,
    note: str | None | object = _UNSET,
) -> Entry:
    entry = require_entry(session, entry_id)
    if value is not _UNSET:
        metric = metric_by_id(session, entry.metric_id)
        value_num, value_bool, value_text = split_value(ValueType(metric.value_type), value)
        entry.value_num = value_num
        entry.value_bool = value_bool
        entry.value_text = value_text
    if occurred_on is not _UNSET:
        entry.occurred_on = _require_date(occurred_on)
    if occurred_at is not _UNSET:
        if occurred_at is not None and not isinstance(occurred_at, datetime):
            raise ValidationError("occurred_at must be a datetime or None")
        entry.occurred_at = _as_utc(occurred_at) if isinstance(occurred_at, datetime) else None
    if note is not _UNSET:
        if note is not None and not isinstance(note, str):
            raise ValidationError("note must be a string or None")
        entry.note = note
    session.add(entry)
    _sync_linked_screen_session(session, entry)
    session.commit()
    session.refresh(entry)
    return entry


def delete_entry(session: Session, entry_id: int) -> None:
    entry = require_entry(session, entry_id)
    _delete_linked_screen_session(session, entry_id)
    session.delete(entry)
    session.commit()


def split_value(
    value_type: ValueType, value: float | bool | str | None
) -> tuple[float | None, bool | None, str | None]:
    if value_type is ValueType.BOOL:
        if value is None:
            return None, True, None
        if isinstance(value, bool):
            return None, value, None
        raise ValidationError("bool metrics expect a boolean value, or omit the value for true")
    if value_type is ValueType.TEXT:
        if value is None:
            raise ValidationError("text metrics require a value")
        if isinstance(value, bool) or not isinstance(value, str):
            raise ValidationError("text metrics expect a string value")
        return None, None, value
    if value is None:
        raise ValidationError(f"{value_type} metrics require a numeric value")
    if isinstance(value, bool | str):
        raise ValidationError(f"{value_type} metrics expect a numeric value")
    return float(value), None, None


def _link_screen_session(session: Session, entry: Entry) -> None:
    if entry.id is None or entry.value_num is None or entry.value_num <= 0:
        return
    app = session.exec(select(ScreenApp).where(ScreenApp.metric_id == entry.metric_id)).first()
    if app is None:
        return
    existing = session.exec(select(ScreenSession).where(ScreenSession.entry_id == entry.id)).first()
    if existing is not None:
        return
    session.add(
        ScreenSession(
            app_id=app.id,
            minutes=entry.value_num,
            occurred_on=entry.occurred_on,
            note=entry.note,
            source=entry.source,
            entry_id=entry.id,
        )
    )


def _sync_linked_screen_session(session: Session, entry: Entry) -> None:
    row = session.exec(select(ScreenSession).where(ScreenSession.entry_id == entry.id)).first()
    if row is None:
        _link_screen_session(session, entry)
        return
    if entry.value_num is None or entry.value_num <= 0:
        return
    row.started_at = None
    row.ended_at = None
    row.minutes = entry.value_num
    row.occurred_on = entry.occurred_on
    row.note = entry.note
    session.add(row)


def _delete_linked_screen_session(session: Session, entry_id: int) -> None:
    row = session.exec(select(ScreenSession).where(ScreenSession.entry_id == entry_id)).first()
    if row is not None:
        session.delete(row)
        session.flush()


def _require_date(value: object) -> date:
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValidationError("occurred_on must be a date")
    return value


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
