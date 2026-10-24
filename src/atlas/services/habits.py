import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, col, select

from atlas.db.models import Area, Entry, Goal, Habit, HabitBreak, Metric
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    HabitKind,
    HabitSpec,
    Period,
    Source,
    TimeOfDay,
    ValueType,
    adherence,
    adherence_counts,
    bucket_for,
    bucket_target,
    current_streak,
    is_satisfied,
    is_scheduled,
    longest_streak,
    rollup,
)
from atlas.services.clock import resolve_today
from atlas.services.entries import delete_entry, log_entry
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    entries_for_metric,
    metric_by_id,
    normalize_weekdays,
    require_active_metric,
    require_goal,
    require_habit,
)
from atlas.services.mapping import entry_view, habit_spec
from atlas.services.metrics import create_metric
from atlas.services.slugs import display_name, normalize_slug

HABITS_AREA_SLUG = "habits"
RECENT_CHECKINS = 30
_UNSET = object()
_SLUG_CHUNK = re.compile(r"[^a-z0-9]+")

# What a habit-first create makes underneath: the metric's type, unit, and direction.
_KIND_METRICS: dict[HabitKind, tuple[ValueType, str | None]] = {
    HabitKind.CHECK: (ValueType.BOOL, None),
    HabitKind.COUNT: (ValueType.COUNT, None),
    HabitKind.DURATION: (ValueType.DURATION, "min"),
    HabitKind.QUIT: (ValueType.COUNT, "slips"),
}


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
    kind: HabitKind = HabitKind.COUNT
    time_of_day: TimeOfDay = TimeOfDay.ANYTIME
    unit: str | None = None
    goal_slug: str | None = None
    archived: bool = False
    bucket_start: date | None = None
    bucket_end: date | None = None
    days_left: int = 0
    effective_target: float | None = None
    excused: bool = False
    skipped_today: bool = False
    today_value: float | None = None
    last_entry_on: date | None = None


@dataclass(frozen=True, slots=True)
class HabitsBoard:
    as_of: date
    scheduled: int
    satisfied: int
    fraction: float | None
    completion_7d: float | None
    completion_30d: float | None
    day: list[HabitStatus]
    week: list[HabitStatus]
    month: list[HabitStatus]


@dataclass(frozen=True, slots=True)
class HabitCheckIn:
    id: int
    occurred_on: date
    value: float | None
    note: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class HabitDetail:
    habit: Habit
    status: HabitStatus
    breaks: list[HabitBreak]
    recent: list[HabitCheckIn]


def create_habit(
    session: Session,
    slug: str | None = None,
    *,
    period: Period,
    target_value: float | None = None,
    comparator: Comparator | None = None,
    metric_slug: str | None = None,
    kind: HabitKind | None = None,
    name: str | None = None,
    unit: str | None = None,
    weekdays: Sequence[int] | None = None,
    time_of_day: TimeOfDay = TimeOfDay.ANYTIME,
    goal_slug: str | None = None,
    active_from: date | None = None,
    active_to: date | None = None,
) -> Habit:
    """Create a habit. Without `metric_slug` its metric is made for it in the Habits area."""
    if slug is None:
        if name is None or not name.strip():
            raise ValidationError("a habit needs a name or a slug")
        slug = slug_from_name(name)
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Habit, slug)
    period = Period(period)
    metric = require_active_metric(session, normalize_slug(metric_slug)) if metric_slug else None
    if metric is not None and ValueType(metric.value_type) is ValueType.TEXT:
        raise ValidationError("habits cannot target a text metric")
    kind = HabitKind(kind) if kind is not None else _kind_for_metric(metric)
    if kind is HabitKind.QUIT:
        period, comparator, target_value, weekdays = Period.DAY, Comparator.AT_MOST, 0.0, None
    comparator = Comparator(comparator) if comparator is not None else Comparator.AT_LEAST
    if target_value is None:
        if kind is not HabitKind.CHECK:
            raise ValidationError(f"a {kind} habit needs a target")
        target_value = 1.0
    if target_value < 0:
        raise ValidationError("target_value must not be negative")
    goal = require_goal(session, normalize_slug(goal_slug)) if goal_slug else None
    if active_from is None:
        active_from = resolve_today(None)
    if active_to is not None and active_to < active_from:
        raise ValidationError("active_to must be on or after active_from")
    normalized_weekdays = normalize_weekdays(weekdays, period)
    if metric is None:
        metric = _create_habit_metric(session, slug, name, kind, comparator, unit)
    habit = Habit(
        metric_id=metric.id,
        slug=slug,
        name=name.strip() if name is not None and name.strip() else display_name(slug),
        period=period,
        target_value=float(target_value),
        comparator=comparator,
        weekdays=normalized_weekdays,
        active_from=active_from,
        active_to=active_to,
        kind=kind,
        time_of_day=TimeOfDay(time_of_day),
        goal_id=goal.id if goal is not None else None,
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def slug_from_name(name: str) -> str:
    slug = _SLUG_CHUNK.sub("-", name.strip().lower()).strip("-")
    if not slug:
        raise ValidationError(f"cannot derive a slug from {name!r}")
    return slug


def list_habits(
    session: Session,
    *,
    metric_slug: str | None = None,
    include_archived: bool = True,
) -> list[Habit]:
    statement = select(Habit).order_by(Habit.slug)
    if metric_slug is not None:
        metric = require_active_metric(session, normalize_slug(metric_slug))
        statement = statement.where(Habit.metric_id == metric.id)
    if not include_archived:
        statement = statement.where(col(Habit.archived_at).is_(None))
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
    time_of_day: TimeOfDay | None = None,
    goal_slug: str | None | object = _UNSET,
    unit: str | None | object = _UNSET,
) -> Habit:
    habit = require_habit(session, normalize_slug(slug))
    kind = HabitKind(habit.kind)
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        habit.name = name.strip()
    if target_value is not None:
        if kind is HabitKind.QUIT:
            raise ValidationError("a quit habit always targets zero slips")
        if target_value < 0:
            raise ValidationError("target_value must not be negative")
        habit.target_value = float(target_value)
    if comparator is not None:
        if kind is HabitKind.QUIT:
            raise ValidationError("a quit habit is always at_most zero")
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
    if time_of_day is not None:
        habit.time_of_day = TimeOfDay(time_of_day)
    if goal_slug is not _UNSET:
        habit.goal_id = (
            require_goal(session, normalize_slug(goal_slug)).id
            if isinstance(goal_slug, str) and goal_slug
            else None
        )
    if unit is not _UNSET:
        metric = metric_by_id(session, habit.metric_id)
        metric.unit = (unit.strip() or None) if isinstance(unit, str) else None
        session.add(metric)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def archive_habit(session: Session, slug: str) -> Habit:
    habit = require_habit(session, normalize_slug(slug))
    if habit.archived_at is not None:
        raise ValidationError(f"habit {habit.slug!r} is already archived")
    habit.archived_at = datetime.now(UTC)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def unarchive_habit(session: Session, slug: str) -> Habit:
    habit = require_habit(session, normalize_slug(slug))
    habit.archived_at = None
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def delete_habit(session: Session, slug: str) -> None:
    """Delete the habit and its breaks. Logged entries stay; a metric made for it is archived."""
    habit = require_habit(session, normalize_slug(slug))
    for row in session.exec(select(HabitBreak).where(HabitBreak.habit_id == habit.id)).all():
        session.delete(row)
    session.flush()
    metric = metric_by_id(session, habit.metric_id)
    session.delete(habit)
    session.flush()
    area = session.get(Area, metric.area_id)
    still_used = session.exec(select(Habit).where(Habit.metric_id == metric.id)).first()
    if area is not None and area.slug == HABITS_AREA_SLUG and still_used is None:
        metric.archived_at = datetime.now(UTC)
        session.add(metric)
    session.commit()


def add_habit_break(
    session: Session,
    slug: str,
    start_on: date | None = None,
    end_on: date | None = None,
    *,
    note: str | None = None,
) -> HabitBreak:
    """Pause a habit for a date range; one day (default today) is a skip."""
    habit = require_habit(session, normalize_slug(slug))
    start_on = resolve_today(None) if start_on is None else start_on
    end_on = start_on if end_on is None else end_on
    if end_on < start_on:
        raise ValidationError("end_on must be on or after start_on")
    row = HabitBreak(
        habit_id=habit.id,
        start_on=start_on,
        end_on=end_on,
        note=(note.strip() or None) if isinstance(note, str) else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_habit_breaks(session: Session, slug: str) -> list[HabitBreak]:
    habit = require_habit(session, normalize_slug(slug))
    return _breaks_for(session, habit)


def delete_habit_break(session: Session, slug: str, break_id: int) -> None:
    habit = require_habit(session, normalize_slug(slug))
    row = session.get(HabitBreak, break_id)
    if row is None or row.habit_id != habit.id:
        raise NotFoundError("habit_break", break_id)
    session.delete(row)
    session.commit()


def check_in(
    session: Session,
    slug: str,
    *,
    amount: float | None = None,
    on: date | None = None,
    note: str | None = None,
    as_of: date | None = None,
    source: Source = Source.CLI,
) -> HabitStatus:
    """Record progress for a day: mark a check habit done, add to a count or timer, or log
    a slip on a quit habit."""
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    today = resolve_today(as_of)
    day = today if on is None else on
    if day > today:
        raise ValidationError("cannot check in on a future day")
    kind = HabitKind(habit.kind)
    if ValueType(metric.value_type) is ValueType.BOOL:
        if not any(entry.value_bool for entry in _entries_on(session, metric, day)):
            log_entry(session, metric.slug, True, occurred_on=day, note=note, source=source)
    else:
        if amount is None:
            amount = 1.0 if kind in (HabitKind.COUNT, HabitKind.QUIT) else None
        if amount is None or amount <= 0:
            raise ValidationError("amount must be a positive number")
        log_entry(session, metric.slug, float(amount), occurred_on=day, note=note, source=source)
    return _status_for(session, habit, metric, today)


def undo_check_in(
    session: Session,
    slug: str,
    *,
    on: date | None = None,
    as_of: date | None = None,
) -> HabitStatus:
    """Remove the latest check-in on a day (all of them for a yes/no habit)."""
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    today = resolve_today(as_of)
    day_entries = _entries_on(session, metric, today if on is None else on)
    if not day_entries:
        raise ValidationError("nothing logged on that day to undo")
    if ValueType(metric.value_type) is ValueType.BOOL:
        targets = day_entries
    else:
        targets = [max(day_entries, key=lambda entry: (entry.created_at, entry.id or 0))]
    for entry in targets:
        delete_entry(session, entry.id)
    return _status_for(session, habit, metric, today)


def habit_status(session: Session, slug: str, *, as_of: date | None = None) -> HabitStatus:
    as_of = resolve_today(as_of)
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    return _status_for(session, habit, metric, as_of)


def habit_detail(session: Session, slug: str, *, as_of: date | None = None) -> HabitDetail:
    as_of = resolve_today(as_of)
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    entries = sorted(
        entries_for_metric(session, metric.id),
        key=lambda entry: (entry.occurred_on, entry.created_at, entry.id or 0),
        reverse=True,
    )
    recent = [
        HabitCheckIn(
            id=entry.id or 0,
            occurred_on=entry.occurred_on,
            value=entry_view(entry).numeric_value(),
            note=entry.note,
            created_at=entry.created_at,
        )
        for entry in entries[:RECENT_CHECKINS]
    ]
    return HabitDetail(
        habit=habit,
        status=_status_for(session, habit, metric, as_of),
        breaks=sorted(_breaks_for(session, habit), key=lambda row: row.start_on, reverse=True),
        recent=recent,
    )


def set_habit_day(
    session: Session,
    slug: str,
    day: date,
    *,
    done: bool,
    as_of: date | None = None,
    source: Source = Source.CLI,
) -> HabitStatus:
    habit = require_habit(session, normalize_slug(slug))
    metric = metric_by_id(session, habit.metric_id)
    if ValueType(metric.value_type) is not ValueType.BOOL:
        raise ValidationError(
            f"habit {habit.slug!r} measures a {metric.value_type} metric; log a value instead"
        )
    day_entries = _entries_on(session, metric, day)
    if done:
        if not any(entry.value_bool for entry in day_entries):
            log_entry(session, metric.slug, True, occurred_on=day, source=source)
    else:
        for entry in day_entries:
            delete_entry(session, entry.id)
    return _status_for(session, habit, metric, resolve_today(as_of))


def habit_statuses(session: Session, *, as_of: date | None = None) -> list[HabitStatus]:
    as_of = resolve_today(as_of)
    return [_status_for(session, habit, metric, as_of) for habit, metric in active_habits(session)]


def habits_board(session: Session, *, as_of: date | None = None) -> HabitsBoard:
    as_of = resolve_today(as_of)
    pairs = active_habits(session)
    statuses = [_status_for(session, habit, metric, as_of) for habit, metric in pairs]
    judged_rows = [status for status in statuses if status.scheduled and not status.excused]
    scheduled = len(judged_rows)
    satisfied = sum(1 for status in judged_rows if status.satisfied)
    return HabitsBoard(
        as_of=as_of,
        scheduled=scheduled,
        satisfied=satisfied,
        fraction=None if scheduled == 0 else satisfied / scheduled,
        completion_7d=_pooled_completion(session, pairs, as_of, days=7),
        completion_30d=_pooled_completion(session, pairs, as_of, days=30),
        day=[status for status in statuses if status.period is Period.DAY],
        week=[status for status in statuses if status.period is Period.WEEK],
        month=[status for status in statuses if status.period is Period.MONTH],
    )


def active_habits(session: Session) -> list[tuple[Habit, Metric]]:
    rows: list[tuple[Habit, Metric]] = []
    for habit in session.exec(select(Habit).order_by(Habit.slug)).all():
        if habit.archived_at is not None:
            continue
        metric = metric_by_id(session, habit.metric_id)
        if metric.archived_at is not None:
            continue
        area = session.get(Area, metric.area_id)
        if area is None or area.archived_at is not None:
            continue
        rows.append((habit, metric))
    return rows


def spec_for(session: Session, habit: Habit, metric: Metric) -> HabitSpec:
    return habit_spec(habit, metric, breaks=_breaks_for(session, habit))


def _status_for(session: Session, habit: Habit, metric: Metric, as_of: date) -> HabitStatus:
    spec = spec_for(session, habit, metric)
    views = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
    bucket = bucket_for(as_of, spec.period)
    scheduled = is_scheduled(spec, bucket, as_of)
    in_bucket = [
        view for view in views if bucket.start <= view.occurred_on <= min(bucket.end, as_of)
    ]
    current_value = rollup(in_bucket, spec.aggregation)
    target = bucket_target(spec, bucket)
    goal = session.get(Goal, habit.goal_id) if habit.goal_id is not None else None
    logged_days = [view.occurred_on for view in views if (view.numeric_value() or 0) > 0]
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
        satisfied=is_satisfied(current_value, spec.comparator, target or spec.target_value),
        scheduled=scheduled,
        as_of=as_of,
        kind=HabitKind(habit.kind),
        time_of_day=TimeOfDay(habit.time_of_day),
        unit=metric.unit,
        goal_slug=goal.slug if goal is not None else None,
        archived=habit.archived_at is not None,
        bucket_start=bucket.start,
        bucket_end=bucket.end,
        days_left=max(0, (bucket.end - as_of).days),
        effective_target=target,
        excused=target is None,
        skipped_today=spec.on_break(as_of),
        today_value=rollup([view for view in views if view.occurred_on == as_of], spec.aggregation),
        last_entry_on=max((day for day in logged_days if day <= as_of), default=None),
    )


def _pooled_completion(
    session: Session,
    pairs: list[tuple[Habit, Metric]],
    as_of: date,
    *,
    days: int,
) -> float | None:
    start = as_of - timedelta(days=days - 1)
    satisfied = 0
    judged = 0
    for habit, metric in pairs:
        views = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
        done, counted = adherence_counts(spec_for(session, habit, metric), views, start, as_of)
        satisfied += done
        judged += counted
    return None if judged == 0 else satisfied / judged


def _breaks_for(session: Session, habit: Habit) -> list[HabitBreak]:
    return list(session.exec(select(HabitBreak).where(HabitBreak.habit_id == habit.id)).all())


def _entries_on(session: Session, metric: Metric, day: date) -> list[Entry]:
    return [entry for entry in entries_for_metric(session, metric.id) if entry.occurred_on == day]


def _kind_for_metric(metric: Metric | None) -> HabitKind:
    if metric is None:
        return HabitKind.CHECK
    match ValueType(metric.value_type):
        case ValueType.BOOL:
            return HabitKind.CHECK
        case ValueType.DURATION:
            return HabitKind.DURATION
        case _:
            return HabitKind.COUNT


def _create_habit_metric(
    session: Session,
    slug: str,
    name: str | None,
    kind: HabitKind,
    comparator: Comparator,
    unit: str | None,
) -> Metric:
    _ensure_habits_area(session)
    value_type, default_unit = _KIND_METRICS[kind]
    lower_is_better = kind is HabitKind.QUIT or comparator is Comparator.AT_MOST
    return create_metric(
        session,
        _free_metric_slug(session, slug),
        area_slug=HABITS_AREA_SLUG,
        value_type=value_type,
        aggregation=Aggregation.SUM,
        name=name.strip() if name is not None and name.strip() else display_name(slug),
        unit=(unit.strip() or None) if unit is not None else default_unit,
        direction=Direction.LOWER_IS_BETTER if lower_is_better else Direction.HIGHER_IS_BETTER,
    )


def _ensure_habits_area(session: Session) -> Area:
    area = session.exec(select(Area).where(Area.slug == HABITS_AREA_SLUG)).first()
    if area is not None:
        if area.archived_at is not None:
            area.archived_at = None
            session.add(area)
            session.flush()
        return area
    area = Area(
        slug=HABITS_AREA_SLUG,
        name="Habits",
        description="Measurements created for habits.",
    )
    session.add(area)
    session.flush()
    return area


def _free_metric_slug(session: Session, slug: str) -> str:
    taken = set(session.exec(select(Metric.slug)).all())
    if slug not in taken:
        return slug
    index = 2
    while f"{slug}-{index}" in taken:
        index += 1
    return f"{slug}-{index}"
