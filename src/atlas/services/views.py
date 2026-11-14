from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session

from atlas.domain import (
    Comparator,
    HabitKind,
    Period,
    bucket_for,
    is_satisfied,
    is_scheduled,
    rollup,
)
from atlas.services.clock import resolve_today
from atlas.services.habits import (
    active_habits,
    habit_status,
    spec_for,
)
from atlas.services.lookups import (
    entries_for_metric,
)
from atlas.services.mapping import entry_view


@dataclass(frozen=True, slots=True)
class WeekDayCell:
    day: date
    scheduled: bool
    value: float | None
    satisfied: bool | None
    excused: bool = False


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
    kind: HabitKind = HabitKind.COUNT
    weekdays: list[int] | None = None


@dataclass(frozen=True, slots=True)
class HabitsCalendar:
    as_of: date
    period: Period
    range_start: date
    range_end: date
    habits: list[WeekHabit]


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
        spec = spec_for(session, habit, metric)
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
            excused = scheduled and spec.on_break(cursor)
            satisfied: bool | None
            if spec.period is Period.DAY and scheduled and not excused and cursor <= as_of:
                satisfied = is_satisfied(value, spec.comparator, spec.target_value)
            else:
                satisfied = None
            days.append(
                WeekDayCell(
                    day=cursor,
                    scheduled=scheduled,
                    value=value,
                    satisfied=satisfied,
                    excused=excused,
                )
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
                kind=HabitKind(habit.kind),
                weekdays=sorted(habit.weekdays) if habit.weekdays else None,
            )
        )
    return HabitsCalendar(
        as_of=as_of,
        period=period,
        range_start=window.start,
        range_end=window.end,
        habits=habits,
    )
