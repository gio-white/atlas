from dataclasses import dataclass
from datetime import date

from sqlmodel import Session

from atlas.domain import Period, bucket_for, previous_bucket
from atlas.services.clock import resolve_today
from atlas.services.screen import screen_minutes_in_range
from atlas.services.tasks import tasks_done_in_week


@dataclass(frozen=True, slots=True)
class HomeWeek:
    as_of: date
    week_start: date
    week_end: date
    focus_minutes: float
    focus_minutes_last_week: float
    focus_delta: float | None
    tasks_done: float
    tasks_done_last_week: float
    tasks_delta: float | None


def home_week(session: Session, *, as_of: date | None = None) -> HomeWeek:
    as_of = resolve_today(as_of)
    week = bucket_for(as_of, Period.WEEK)
    previous = previous_bucket(week)
    this_focus = screen_minutes_in_range(session, week.start, min(week.end, as_of))
    last_focus = screen_minutes_in_range(session, previous.start, previous.end)
    this_tasks = float(tasks_done_in_week(session, as_of=as_of))
    last_tasks = float(tasks_done_in_week(session, as_of=previous.end))
    return HomeWeek(
        as_of=as_of,
        week_start=week.start,
        week_end=week.end,
        focus_minutes=this_focus,
        focus_minutes_last_week=last_focus,
        focus_delta=_delta(this_focus, last_focus),
        tasks_done=this_tasks,
        tasks_done_last_week=last_tasks,
        tasks_delta=_delta(this_tasks, last_tasks),
    )


def _delta(this_week: float, last_week: float) -> float | None:
    if last_week == 0:
        return None
    return (this_week - last_week) / last_week
