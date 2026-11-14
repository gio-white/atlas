from collections.abc import Sequence

from sqlmodel import Session, col, select

from atlas.db.models import (
    Entry,
    Habit,
    LibraryTitle,
    LibraryTopic,
    Metric,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    ScreenDevice,
    ScreenSession,
    SleepSession,
)
from atlas.domain import Period
from atlas.services.errors import AlreadyExistsError, NotFoundError, ValidationError


def require_metric(session: Session, slug: str) -> Metric:
    row = session.exec(select(Metric).where(Metric.slug == slug)).first()
    if row is None:
        raise NotFoundError("metric", slug)
    return row


def require_habit(session: Session, slug: str) -> Habit:
    row = session.exec(select(Habit).where(Habit.slug == slug)).first()
    if row is None:
        raise NotFoundError("habit", slug)
    return row


def require_screen_category(session: Session, slug: str) -> ScreenCategory:
    row = session.exec(select(ScreenCategory).where(ScreenCategory.slug == slug)).first()
    if row is None:
        raise NotFoundError("screen_category", slug)
    return row


def require_screen_app(session: Session, slug: str) -> ScreenApp:
    row = session.exec(select(ScreenApp).where(ScreenApp.slug == slug)).first()
    if row is None:
        raise NotFoundError("screen_app", slug)
    return row


def require_screen_budget(session: Session, slug: str) -> ScreenBudget:
    row = session.exec(select(ScreenBudget).where(ScreenBudget.slug == slug)).first()
    if row is None:
        raise NotFoundError("screen_budget", slug)
    return row


def require_screen_device(session: Session, slug: str) -> ScreenDevice:
    row = session.exec(select(ScreenDevice).where(ScreenDevice.slug == slug)).first()
    if row is None:
        raise NotFoundError("screen_device", slug)
    return row


def require_screen_session(session: Session, session_id: int) -> ScreenSession:
    row = session.get(ScreenSession, session_id)
    if row is None:
        raise NotFoundError("screen_session", session_id)
    return row


def require_sleep_session(session: Session, session_id: int) -> SleepSession:
    row = session.get(SleepSession, session_id)
    if row is None:
        raise NotFoundError("sleep_session", session_id)
    return row


def require_library_topic(session: Session, slug: str) -> LibraryTopic:
    row = session.exec(select(LibraryTopic).where(LibraryTopic.slug == slug)).first()
    if row is None:
        raise NotFoundError("library_topic", slug)
    return row


def require_library_title(session: Session, slug: str) -> LibraryTitle:
    row = session.exec(select(LibraryTitle).where(LibraryTitle.slug == slug)).first()
    if row is None:
        raise NotFoundError("library_title", slug)
    return row


def require_entry(session: Session, entry_id: int) -> Entry:
    row = session.get(Entry, entry_id)
    if row is None:
        raise NotFoundError("entry", entry_id)
    return row


def require_active_metric(session: Session, slug: str) -> Metric:
    metric = require_metric(session, slug)
    if metric.archived_at is not None:
        raise ValidationError(f"metric {slug!r} is archived")
    return metric


def ensure_unique_slug(
    session: Session,
    model: type[Metric]
    | type[Habit]
    | type[ScreenCategory]
    | type[ScreenApp]
    | type[ScreenBudget]
    | type[ScreenDevice]
    | type[LibraryTopic]
    | type[LibraryTitle],
    slug: str,
) -> None:
    if session.exec(select(model).where(model.slug == slug)).first() is not None:
        raise AlreadyExistsError(model.__tablename__, slug)


def entries_for_metric(session: Session, metric_id: int) -> list[Entry]:
    return list(session.exec(select(Entry).where(Entry.metric_id == metric_id)).all())


def metric_by_id(session: Session, metric_id: int) -> Metric:
    metric = session.get(Metric, metric_id)
    if metric is None:
        raise NotFoundError("metric", metric_id)
    return metric


def normalize_weekdays(weekdays: Sequence[int] | None, period: Period) -> list[int] | None:
    if weekdays is None:
        return None
    if period is not Period.DAY:
        raise ValidationError("weekdays are only valid when period is day")
    values = sorted({int(day) for day in weekdays})
    if not values:
        raise ValidationError("weekdays must not be empty")
    if any(day < 1 or day > 7 for day in values):
        raise ValidationError("weekdays must be ISO weekdays 1-7 (Mon-Sun)")
    return values


def not_archived(column):
    return col(column).is_(None)
