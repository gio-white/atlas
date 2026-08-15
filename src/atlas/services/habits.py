from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel import Session, select

from atlas.db.models import Area, Habit, Metric
from atlas.domain import (
    Comparator,
    Period,
    ValueType,
    adherence,
    bucket_for,
    current_streak,
    is_satisfied,
    is_scheduled,
    longest_streak,
    rollup,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    entries_for_metric,
    metric_by_id,
    normalize_weekdays,
    require_active_metric,
    require_habit,
)
from atlas.services.mapping import entry_view, habit_spec
from atlas.services.slugs import display_name, normalize_slug

_UNSET = object()


@dataclass(frozen=True, slots=True)
class HabitStatus:
    slug: str
    name: str
    metric_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_streak: int
    longest_streak: int
    adherence: float | None
    current_value: float | None
    satisfied: bool
    scheduled: bool
    as_of: date


@dataclass(frozen=True, slots=True)
class HabitsBoard:
    as_of: date
    scheduled: int
    satisfied: int
    fraction: float | None
    day: list[HabitStatus]
    week: list[HabitStatus]
    month: list[HabitStatus]


def create_habit(
    session: Session,
    slug: str,
    *,
    metric_slug: str,
    period: Period,
    target_value: float,
    comparator: Comparator,
    name: str | None = None,
    weekdays: Sequence[int] | None = None,
    active_from: date | None = None,
    active_to: date | None = None,
) -> Habit:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Habit, slug)
    metric = require_active_metric(session, normalize_slug(metric_slug))
    if ValueType(metric.value_type) is ValueType.TEXT:
        raise ValidationError("habits cannot target a text metric")
    if active_from is None:
        active_from = resolve_today(None)
    if active_to is not None and active_to < active_from:
        raise ValidationError("active_to must be on or after active_from")
    habit = Habit(
        metric_id=metric.id,
        slug=slug,
        name=name if name is not None else display_name(slug),
        period=period,
        target_value=float(target_value),
        comparator=comparator,
        weekdays=normalize_weekdays(weekdays, period),
        active_from=active_from,
        active_to=active_to,
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def list_habits(session: Session, *, metric_slug: str | None = None) -> list[Habit]:
    statement = select(Habit).order_by(Habit.slug)
    if metric_slug is not None:
        metric = require_active_metric(session, normalize_slug(metric_slug))
        statement = statement.where(Habit.metric_id == metric.id)
    return list(session.exec(statement).all())


def get_habit(session: Session, slug: str) -> Habit:
    return require_habit(session, normalize_slug(slug))


def update_habit(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    target_value: float | None = None,
    comparator: Comparator | None = None,
    weekdays: Sequence[int] | None | object = _UNSET,
    active_to: date | None | object = _UNSET,
) -> Habit:
    habit = require_habit(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        habit.name = name
    if target_value is not None:
        habit.target_value = float(target_value)
    if comparator is not None:
        habit.comparator = comparator
    if weekdays is not _UNSET:
        if weekdays is not None and not isinstance(weekdays, Sequence):
            raise ValidationError("weekdays must be a list of ISO weekdays or None")
        habit.weekdays = normalize_weekdays(
            None if weekdays is None else [int(day) for day in weekdays],
            Period(habit.period),
        )
    if active_to is not _UNSET:
        if active_to is not None and (
            isinstance(active_to, datetime) or not isinstance(active_to, date)
        ):
            raise ValidationError("active_to must be a date or None")
        if isinstance(active_to, date) and active_to < habit.active_from:
            raise ValidationError("active_to must be on or after active_from")
        habit.active_to = active_to
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def habit_status(session: Session, slug: str, *, as_of: date | None = None) -> HabitStatus:
    as_of = resolve_today(as_of)
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    return _status_for(session, habit, metric, as_of)


def habit_statuses(session: Session, *, as_of: date | None = None) -> list[HabitStatus]:
    as_of = resolve_today(as_of)
    return [_status_for(session, habit, metric, as_of) for habit, metric in active_habits(session)]


def habits_board(session: Session, *, as_of: date | None = None) -> HabitsBoard:
    as_of = resolve_today(as_of)
    statuses = habit_statuses(session, as_of=as_of)
    scheduled_rows = [status for status in statuses if status.scheduled]
    satisfied_rows = [status for status in scheduled_rows if status.satisfied]
    scheduled = len(scheduled_rows)
    satisfied = len(satisfied_rows)
    fraction = None if scheduled == 0 else satisfied / scheduled
    return HabitsBoard(
        as_of=as_of,
        scheduled=scheduled,
        satisfied=satisfied,
        fraction=fraction,
        day=[status for status in statuses if status.period is Period.DAY],
        week=[status for status in statuses if status.period is Period.WEEK],
        month=[status for status in statuses if status.period is Period.MONTH],
    )


def active_habits(session: Session) -> list[tuple[Habit, Metric]]:
    rows: list[tuple[Habit, Metric]] = []
    for habit in session.exec(select(Habit).order_by(Habit.slug)).all():
        metric = metric_by_id(session, habit.metric_id)
        if metric.archived_at is not None:
            continue
        area = session.get(Area, metric.area_id)
        if area is None or area.archived_at is not None:
            continue
        rows.append((habit, metric))
    return rows


def _status_for(session: Session, habit: Habit, metric: Metric, as_of: date) -> HabitStatus:
    spec = habit_spec(habit, metric)
    views = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
    bucket = bucket_for(as_of, spec.period)
    scheduled = is_scheduled(spec, bucket, as_of)
    in_bucket = [
        view for view in views if bucket.start <= view.occurred_on <= min(bucket.end, as_of)
    ]
    current_value = rollup(in_bucket, spec.aggregation)
    return HabitStatus(
        slug=habit.slug,
        name=habit.name,
        metric_slug=metric.slug,
        period=spec.period,
        target_value=spec.target_value,
        comparator=spec.comparator,
        current_streak=current_streak(spec, views, as_of),
        longest_streak=longest_streak(spec, views, as_of),
        adherence=adherence(spec, views, spec.active_from, as_of),
        current_value=current_value,
        satisfied=is_satisfied(current_value, spec.comparator, spec.target_value),
        scheduled=scheduled,
        as_of=as_of,
    )
