"""This week: the numbers of one Monday-to-`as_of` window, each from its section's own rule.

`week_numbers` computes one window; `this_week` adds the same window one week earlier for the
comparison and each habit's part of Habits kept; `week_so_far` is Home's four of them. Nothing
here is stored.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, col, func, select

from atlas.db.models import Milestone, Task, TimeBlock
from atlas.domain import Period, QuestStatus, TaskStatus
from atlas.domain.quests import as_utc, sessions_kept
from atlas.services.clock import resolve_today
from atlas.services.habit_views import habits_kept, habits_kept_by_habit
from atlas.services.library import library_dashboard
from atlas.services.quest_views import local_day_bounds
from atlas.services.quests import block_view
from atlas.services.screen import screen_dashboard
from atlas.services.sleep import sleep_view


@dataclass(frozen=True, slots=True)
class WeekNumbers:
    """One window, from `week_start` (a Monday) to `as_of`, both local dates, inclusive."""

    as_of: date
    week_start: date
    sessions_kept: int
    sessions_total: int
    tasks_completed: int
    milestones_completed: int
    habits_kept: int
    habits_judged: int
    habits_kept_share: float | None
    sleep_average_minutes: float | None
    sleep_average_bedtime: float | None
    sleep_average_wake: float | None
    sleep_nights: int
    sleep_missing_nights: int
    screen_total: float | None
    screen_daily_average: float | None
    screen_score: int | None
    screen_good: float | None
    screen_neutral: float | None
    screen_bad: float | None
    titles_finished: int


@dataclass(frozen=True, slots=True)
class WeekHabit:
    """An active habit on This week with its part of Habits kept: Done (capped at the target)
    over the target for Monday to `as_of`. The rows add up to Habits kept."""

    slug: str
    name: str
    done: int
    target: int


@dataclass(frozen=True, slots=True)
class ThisWeek:
    """The week holding `as_of`, counted up to `as_of`, against the same days a week earlier.

    `complete` is true once `as_of` is the Sunday, so the whole week is counted. `previous`
    covers the same weekdays of the week before, so a week in progress is compared like for like.
    """

    as_of: date
    week_start: date
    week_end: date
    complete: bool
    current: WeekNumbers
    previous: WeekNumbers
    habits: list[WeekHabit]


@dataclass(frozen=True, slots=True)
class WeekSoFar:
    as_of: date
    week_start: date
    sessions_kept: int
    sessions_total: int
    habits_kept: int
    habits_judged: int
    habits_kept_share: float | None
    sleep_average_minutes: float | None
    sleep_nights: int
    screen_score: int | None


def week_numbers(session: Session, *, as_of: date, now: datetime | None = None) -> WeekNumbers:
    monday = as_of - timedelta(days=as_of.weekday())
    week_start, _ = local_day_bounds(monday)
    _, day_end = local_day_bounds(as_of)
    # Looking back at a past day, "now" is the end of that day: later answers do not exist yet.
    now = min(as_utc(now) if now is not None else datetime.now(UTC), day_end)
    start_naive, end_naive = week_start.replace(tzinfo=None), day_end.replace(tzinfo=None)

    blocks = session.exec(
        select(TimeBlock).where(
            col(TimeBlock.start_at) >= start_naive, col(TimeBlock.start_at) < end_naive
        )
    ).all()
    kept = sessions_kept([block_view(row) for row in blocks], week_start, day_end, now)
    tasks = session.exec(
        select(func.count())
        .select_from(Task)
        .where(
            Task.status == TaskStatus.COMPLETED,
            col(Task.completed_at) >= start_naive,
            col(Task.completed_at) < end_naive,
        )
    ).one()
    milestones = session.exec(
        select(func.count())
        .select_from(Milestone)
        .where(
            Milestone.status == QuestStatus.COMPLETED,
            col(Milestone.completed_at) >= start_naive,
            col(Milestone.completed_at) < end_naive,
        )
    ).one()

    habits = habits_kept(session, monday, as_of, now=now)
    days = (as_of - monday).days + 1
    sleep = sleep_view(session, as_of=as_of, days=days)
    screen = screen_dashboard(session, as_of=as_of, period=Period.WEEK)
    library = library_dashboard(session, as_of=as_of, period=Period.WEEK)
    return WeekNumbers(
        as_of=as_of,
        week_start=monday,
        sessions_kept=kept.kept,
        sessions_total=kept.total,
        tasks_completed=tasks,
        milestones_completed=milestones,
        habits_kept=habits.done,
        habits_judged=habits.target,
        habits_kept_share=habits.share,
        sleep_average_minutes=sleep.average_asleep,
        sleep_average_bedtime=sleep.average_bed_offset,
        sleep_average_wake=sleep.average_wake_offset,
        sleep_nights=sleep.nights_logged,
        sleep_missing_nights=days - sleep.nights_logged,
        screen_total=screen.total,
        screen_daily_average=screen.daily_average,
        screen_score=screen.score,
        screen_good=screen.judgments.useful,
        screen_neutral=screen.judgments.neutral,
        screen_bad=screen.judgments.waste,
        titles_finished=library.finished_in_range,
    )


def this_week(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> ThisWeek:
    as_of = resolve_today(as_of)
    current = week_numbers(session, as_of=as_of, now=now)
    previous = week_numbers(session, as_of=as_of - timedelta(days=7), now=now)
    week_end = current.week_start + timedelta(days=6)
    return ThisWeek(
        as_of=as_of,
        week_start=current.week_start,
        week_end=week_end,
        complete=as_of >= week_end,
        current=current,
        previous=previous,
        habits=[
            WeekHabit(slug=habit.slug, name=habit.name, done=figure.done, target=figure.target)
            for habit, figure in habits_kept_by_habit(session, current.week_start, as_of, now=now)
        ],
    )


def week_so_far(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> WeekSoFar:
    numbers = week_numbers(session, as_of=resolve_today(as_of), now=now)
    return WeekSoFar(
        as_of=numbers.as_of,
        week_start=numbers.week_start,
        sessions_kept=numbers.sessions_kept,
        sessions_total=numbers.sessions_total,
        habits_kept=numbers.habits_kept,
        habits_judged=numbers.habits_judged,
        habits_kept_share=numbers.habits_kept_share,
        sleep_average_minutes=numbers.sleep_average_minutes,
        sleep_nights=numbers.sleep_nights,
        screen_score=numbers.screen_score,
    )
