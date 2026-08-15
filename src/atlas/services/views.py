from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session, select

from atlas.db.models import Entry, Goal, Habit, Metric
from atlas.domain import (
    Aggregation,
    Comparator,
    GoalStatus,
    Period,
    bucket_for,
    is_satisfied,
    is_scheduled,
    rollup,
)
from atlas.services.clock import resolve_today
from atlas.services.goals import GoalProgressReport, goal_progress
from atlas.services.habits import HabitStatus, active_habits, habit_status, habit_statuses
from atlas.services.lookups import (
    entries_for_metric,
    metric_by_id,
    not_archived,
    require_area,
)
from atlas.services.mapping import entry_view, habit_spec
from atlas.services.slugs import normalize_slug


@dataclass(frozen=True, slots=True)
class LoggedEntry:
    id: int
    metric_slug: str
    occurred_on: date
    value_num: float | None
    value_bool: bool | None
    value_text: str | None
    note: str | None


@dataclass(frozen=True, slots=True)
class TodayView:
    as_of: date
    habits: list[HabitStatus]
    entries: list[LoggedEntry]
    goals: list[GoalProgressReport]


@dataclass(frozen=True, slots=True)
class WeekDayCell:
    day: date
    scheduled: bool
    value: float | None
    satisfied: bool | None


@dataclass(frozen=True, slots=True)
class WeekHabit:
    slug: str
    name: str
    metric_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_value: float | None
    satisfied: bool
    current_streak: int
    days: list[WeekDayCell]


@dataclass(frozen=True, slots=True)
class WeekView:
    as_of: date
    week_start: date
    week_end: date
    habits: list[WeekHabit]


@dataclass(frozen=True, slots=True)
class HabitsCalendar:
    as_of: date
    period: Period
    range_start: date
    range_end: date
    habits: list[WeekHabit]


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    slug: str
    name: str
    unit: str | None
    aggregation: Aggregation
    latest_on: date | None
    latest_value: float | None


@dataclass(frozen=True, slots=True)
class AreaView:
    slug: str
    name: str
    description: str | None
    as_of: date
    metrics: list[MetricSnapshot]
    habits: list[HabitStatus]
    goals: list[GoalProgressReport]


def today_view(session: Session, *, as_of: date | None = None) -> TodayView:
    as_of = resolve_today(as_of)
    habits = [status for status in habit_statuses(session, as_of=as_of) if status.scheduled]
    goals = [
        goal_progress(session, goal.slug, as_of=as_of)
        for goal in session.exec(
            select(Goal).where(Goal.status == GoalStatus.ACTIVE).order_by(Goal.slug)
        ).all()
    ]
    return TodayView(
        as_of=as_of,
        habits=habits,
        entries=_logged_on(session, as_of),
        goals=goals,
    )


def week_view(session: Session, *, as_of: date | None = None) -> WeekView:
    calendar = habit_calendar(session, period=Period.WEEK, as_of=as_of)
    return WeekView(
        as_of=calendar.as_of,
        week_start=calendar.range_start,
        week_end=calendar.range_end,
        habits=calendar.habits,
    )


def habit_calendar(
    session: Session,
    *,
    period: Period = Period.WEEK,
    as_of: date | None = None,
) -> HabitsCalendar:
    as_of = resolve_today(as_of)
    window = bucket_for(as_of, period)
    habits: list[WeekHabit] = []
    for habit, metric in active_habits(session):
        spec = habit_spec(habit, metric)
        status = habit_status(session, habit.slug, as_of=as_of)
        views = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
        days: list[WeekDayCell] = []
        cursor = window.start
        while cursor <= window.end:
            day_bucket = bucket_for(cursor, Period.DAY)
            if spec.period is Period.DAY:
                scheduled = is_scheduled(spec, day_bucket, as_of)
            else:
                in_window = spec.active_from <= cursor
                if spec.active_to is not None:
                    in_window = in_window and cursor <= spec.active_to
                scheduled = in_window
            day_views = [view for view in views if view.occurred_on == cursor]
            value = rollup(day_views, spec.aggregation)
            satisfied: bool | None
            if spec.period is Period.DAY and scheduled and cursor <= as_of:
                satisfied = is_satisfied(value, spec.comparator, spec.target_value)
            else:
                satisfied = None
            days.append(
                WeekDayCell(day=cursor, scheduled=scheduled, value=value, satisfied=satisfied)
            )
            cursor = cursor + timedelta(days=1)
        habits.append(
            WeekHabit(
                slug=habit.slug,
                name=habit.name,
                metric_slug=metric.slug,
                period=spec.period,
                target_value=spec.target_value,
                comparator=spec.comparator,
                current_value=status.current_value,
                satisfied=status.satisfied,
                current_streak=status.current_streak,
                days=days,
            )
        )
    return HabitsCalendar(
        as_of=as_of,
        period=period,
        range_start=window.start,
        range_end=window.end,
        habits=habits,
    )


def area_view(session: Session, slug: str, *, as_of: date | None = None) -> AreaView:
    as_of = resolve_today(as_of)
    area = require_area(session, normalize_slug(slug))
    metrics = list(
        session.exec(
            select(Metric)
            .where(Metric.area_id == area.id)
            .where(not_archived(Metric.archived_at))
            .order_by(Metric.slug)
        ).all()
    )
    metric_ids = {metric.id for metric in metrics}
    snapshots = [_snapshot(session, metric, as_of) for metric in metrics]
    habits = [
        habit_status(session, habit.slug, as_of=as_of)
        for habit in session.exec(select(Habit).order_by(Habit.slug)).all()
        if habit.metric_id in metric_ids
    ]
    goals = [
        goal_progress(session, goal.slug, as_of=as_of)
        for goal in session.exec(
            select(Goal).where(Goal.area_id == area.id).order_by(Goal.slug)
        ).all()
        if GoalStatus(goal.status) is not GoalStatus.ABANDONED
    ]
    return AreaView(
        slug=area.slug,
        name=area.name,
        description=area.description,
        as_of=as_of,
        metrics=snapshots,
        habits=habits,
        goals=goals,
    )


def _logged_on(session: Session, as_of: date) -> list[LoggedEntry]:
    entries = list(
        session.exec(select(Entry).where(Entry.occurred_on == as_of).order_by(Entry.id)).all()
    )
    logged: list[LoggedEntry] = []
    for entry in entries:
        metric = metric_by_id(session, entry.metric_id)
        logged.append(
            LoggedEntry(
                id=entry.id,
                metric_slug=metric.slug,
                occurred_on=entry.occurred_on,
                value_num=entry.value_num,
                value_bool=entry.value_bool,
                value_text=entry.value_text,
                note=entry.note,
            )
        )
    return logged


def _snapshot(session: Session, metric: Metric, as_of: date) -> MetricSnapshot:
    views = [
        entry_view(entry)
        for entry in entries_for_metric(session, metric.id)
        if entry.occurred_on <= as_of
    ]
    if not views:
        return MetricSnapshot(
            slug=metric.slug,
            name=metric.name,
            unit=metric.unit,
            aggregation=Aggregation(metric.aggregation),
            latest_on=None,
            latest_value=None,
        )
    latest_on = max(view.occurred_on for view in views)
    latest_value = rollup(
        [view for view in views if view.occurred_on == latest_on],
        Aggregation(metric.aggregation),
    )
    return MetricSnapshot(
        slug=metric.slug,
        name=metric.name,
        unit=metric.unit,
        aggregation=Aggregation(metric.aggregation),
        latest_on=latest_on,
        latest_value=latest_value,
    )
