from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session

from atlas.domain import Aggregation, EntryView, Period, bucket_for, previous_bucket, rollup
from atlas.services.clock import resolve_today
from atlas.services.life import CHECKIN_METRIC_SLUG, ensure_checkin_habit
from atlas.services.lookups import entries_for_metric, require_metric
from atlas.services.mapping import entry_view
from atlas.services.screen import screen_minutes_in_range
from atlas.services.slips import slips_week
from atlas.services.tasks import tasks_done_in_week


@dataclass(frozen=True, slots=True)
class HomeWeek:
    as_of: date
    week_start: date
    week_end: date
    updates: float
    updates_last_week: float
    updates_delta: float | None
    slips: float
    slips_last_week: float
    slips_delta: float | None
    focus_minutes: float
    focus_minutes_last_week: float
    focus_delta: float | None
    tasks_done: float
    tasks_done_last_week: float
    tasks_delta: float | None
    series_updates: list[float]
    series_slips: list[float]


def home_week(session: Session, *, as_of: date | None = None) -> HomeWeek:
    as_of = resolve_today(as_of)
    ensure_checkin_habit(session)
    slips = slips_week(session, as_of=as_of)
    week = bucket_for(as_of, Period.WEEK)
    previous = previous_bucket(week)
    checkin = require_metric(session, CHECKIN_METRIC_SLUG)
    checkin_views = [entry_view(entry) for entry in entries_for_metric(session, checkin.id)]
    this_updates, series_updates = _checkin_series(checkin_views, week.start, as_of)
    last_updates, _ = _checkin_series(checkin_views, previous.start, previous.end)
    this_focus = _screen_minutes(session, week.start, min(week.end, as_of))
    last_focus = _screen_minutes(session, previous.start, previous.end)
    this_tasks = float(tasks_done_in_week(session, as_of=as_of))
    last_tasks = float(tasks_done_in_week(session, as_of=previous.end))
    return HomeWeek(
        as_of=as_of,
        week_start=week.start,
        week_end=week.end,
        updates=this_updates,
        updates_last_week=last_updates,
        updates_delta=_delta(this_updates, last_updates),
        slips=slips.this_week,
        slips_last_week=slips.last_week,
        slips_delta=slips.delta_fraction,
        focus_minutes=this_focus,
        focus_minutes_last_week=last_focus,
        focus_delta=_delta(this_focus, last_focus),
        tasks_done=this_tasks,
        tasks_done_last_week=last_tasks,
        tasks_delta=_delta(this_tasks, last_tasks),
        series_updates=series_updates,
        series_slips=slips.series,
    )


def _checkin_series(
    views: Sequence[EntryView], week_start: date, as_of: date
) -> tuple[float, list[float]]:
    series: list[float] = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        if day > as_of:
            series.append(0.0)
            continue
        value = (
            rollup(
                [view for view in views if view.occurred_on == day],
                Aggregation.SUM,
            )
            or 0.0
        )
        series.append(1.0 if value > 0 else 0.0)
    return sum(series), series


def _screen_minutes(session: Session, start: date, end: date) -> float:
    return screen_minutes_in_range(session, start, end)


def _delta(this_week: float, last_week: float) -> float | None:
    if last_week == 0:
        return None
    return (this_week - last_week) / last_week
