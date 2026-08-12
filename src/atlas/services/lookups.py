from collections.abc import Sequence

from sqlmodel import Session, col, select

from atlas.db.models import Area, Entry, Goal, Habit, Metric, Milestone
from atlas.domain import Period
from atlas.services.errors import AlreadyExistsError, NotFoundError, ValidationError


def require_area(session: Session, slug: str) -> Area:
    row = session.exec(select(Area).where(Area.slug == slug)).first()
    if row is None:
        raise NotFoundError("area", slug)
    return row


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


def require_goal(session: Session, slug: str) -> Goal:
    row = session.exec(select(Goal).where(Goal.slug == slug)).first()
    if row is None:
        raise NotFoundError("goal", slug)
    return row


def require_entry(session: Session, entry_id: int) -> Entry:
    row = session.get(Entry, entry_id)
    if row is None:
        raise NotFoundError("entry", entry_id)
    return row


def require_active_area(session: Session, slug: str) -> Area:
    area = require_area(session, slug)
    if area.archived_at is not None:
        raise ValidationError(f"area {slug!r} is archived")
    return area


def require_active_metric(session: Session, slug: str) -> Metric:
    metric = require_metric(session, slug)
    if metric.archived_at is not None:
        raise ValidationError(f"metric {slug!r} is archived")
    area = session.get(Area, metric.area_id)
    if area is not None and area.archived_at is not None:
        raise ValidationError(f"metric {slug!r} belongs to archived area {area.slug!r}")
    return metric


def ensure_unique_slug(
    session: Session, model: type[Area] | type[Metric] | type[Habit] | type[Goal], slug: str
) -> None:
    if session.exec(select(model).where(model.slug == slug)).first() is not None:
        raise AlreadyExistsError(model.__tablename__, slug)


def entries_for_metric(session: Session, metric_id: int) -> list[Entry]:
    return list(session.exec(select(Entry).where(Entry.metric_id == metric_id)).all())


def milestones_for_goal(session: Session, goal_id: int) -> list[Milestone]:
    statement = select(Milestone).where(Milestone.goal_id == goal_id).order_by(Milestone.id)
    return list(session.exec(statement).all())


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
