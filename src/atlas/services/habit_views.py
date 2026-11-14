"""Habit results for the screens: one day, one week, one habit, and Habits kept (habits brief
§6–§8). Everything is computed on read from rules, marks, freezes, and the data feeds.

The *As of* date is "today": a past date is judged as if that day had just ended, with the data
stored now (habits plan, assumptions).
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlmodel import Session, col, select

from atlas.db.models import Habit, HabitFreeze, HabitMark, HabitRule
from atlas.domain import HabitMarkResult, Period, TimeOfDay
from atlas.domain.enums import HabitCheck
from atlas.domain.habits import (
    Clock,
    DayResult,
    DayStatus,
    HabitFacts,
    PeriodResult,
    RuleSpec,
    best_streak,
    current_streak,
    day_result,
    kept_counts,
    kept_last_4_weeks,
    periods,
    share,
)
from atlas.domain.quests import as_utc
from atlas.services.clock import resolve_today
from atlas.services.habit_data import HabitData
from atlas.services.habits import HabitView, get_habit, habit_view, list_freezes, list_habits
from atlas.settings import load_settings

TIME_OF_DAY_ORDER = (TimeOfDay.MORNING, TimeOfDay.AFTERNOON, TimeOfDay.EVENING, TimeOfDay.ANYTIME)
HISTORY_WEEKS = 12
RECENT_DAYS = 14


@dataclass(frozen=True, slots=True)
class Streak:
    count: int
    period: Period
    """The unit: days, weeks, or months, from the rule in force today."""


@dataclass(frozen=True, slots=True)
class PeriodProgress:
    """A weekly or monthly habit's figure: "2 of 4 this week", "1 of 2 this month"."""

    period: Period
    done: int
    target: int


@dataclass(frozen=True, slots=True)
class HabitResults:
    """One habit's facts and every period through the last day asked for."""

    habit: Habit
    facts: HabitFacts
    clock: Clock
    periods: list[PeriodResult]

    def day(self, day: date) -> DayResult:
        return day_result(self.facts, day, self.clock)

    def streak(self) -> Streak:
        finished = [result for result in self.periods if result.start <= self.clock.today]
        return Streak(current_streak(finished), self.facts.rule_on(self.clock.today).period)

    def progress(self, day: date) -> PeriodProgress | None:
        for result in self.periods:
            if result.period is not Period.DAY and result.start <= day <= result.end:
                return PeriodProgress(result.period, result.done, result.target)
        return None


@dataclass(frozen=True, slots=True)
class HabitDayRow:
    view: HabitView
    result: DayResult
    streak: Streak
    progress: PeriodProgress | None


@dataclass(frozen=True, slots=True)
class DayCount:
    """One day of the week strip: how many of its scheduled, unfrozen habits are done."""

    day: date
    done: int
    total: int


@dataclass(frozen=True, slots=True)
class HabitsDay:
    day: date
    as_of: date
    done: int
    total: int
    week: list[DayCount]
    rows: list[HabitDayRow]


@dataclass(frozen=True, slots=True)
class HabitWeekRow:
    view: HabitView
    days: list[DayResult]
    streak: Streak
    progress: PeriodProgress | None


@dataclass(frozen=True, slots=True)
class KeptFigure:
    done: int
    target: int
    share: float | None


@dataclass(frozen=True, slots=True)
class HabitsWeek:
    as_of: date
    week_start: date
    week_end: date
    rows: list[HabitWeekRow]
    kept: KeptFigure
    """Habits kept this week, Monday to `as_of` (the whole week once it is over)."""
    kept_last_week: KeptFigure
    """The same days one week earlier."""


@dataclass(frozen=True, slots=True)
class HabitDetail:
    view: HabitView
    as_of: date
    current_streak: Streak
    best_streak: int
    kept_last_4_weeks: KeptFigure
    history: list[PeriodResult]
    """The last 12 weeks: one period per day for a daily habit, per week or month otherwise."""
    recent: list[DayResult]
    """The last 14 days, newest first."""
    freezes: list[HabitFreeze]


def habit_clock(as_of: date | None = None, now: datetime | None = None) -> Clock:
    """Today is the As of date. On the real today the clock is the current minute; a past date
    is the whole day, as if it had just ended."""
    settings = load_settings()
    instant = as_utc(now) if now is not None else datetime.now(UTC)
    real_today = instant.astimezone(settings.timezone).date()
    today = resolve_today(as_of) if as_of is not None else real_today
    if today < real_today:
        return Clock(today)
    if today > real_today:
        return Clock(today, 0)
    local = instant.astimezone(settings.timezone)
    return Clock(today, local.hour * 60 + local.minute + local.second / 60)


def habit_results(
    session: Session,
    habits: Sequence[Habit],
    last: date,
    clock: Clock,
) -> list[HabitResults]:
    """Each habit's periods from its first day through `last`, reading each feed once."""
    if not habits:
        return []
    ids = [habit.id for habit in habits]
    rules = _by_habit(session, HabitRule, ids, HabitRule.starts_on)
    marks = _by_habit(session, HabitMark, ids, HabitMark.day)
    freezes = session.exec(select(HabitFreeze)).all()
    shared = [(row.start_on, row.end_on) for row in freezes if row.habit_id is None]
    own: dict[int | None, list[tuple[date, date]]] = defaultdict(list)
    for row in freezes:
        if row.habit_id is not None:
            own[row.habit_id].append((row.start_on, row.end_on))
    specs = {habit.id: [_spec(rule) for rule in rules[habit.id]] for habit in habits}
    data_first = [
        habit.first_day
        for habit in habits
        if any(HabitCheck(spec.check) is HabitCheck.DATA for spec in specs[habit.id])
    ]
    data = HabitData.load(session, min(data_first), last) if data_first else None
    out: list[HabitResults] = []
    for habit in habits:
        bare = HabitFacts(first_day=habit.first_day, rules=tuple(specs[habit.id]))
        readings = {}
        if data is not None:
            day = habit.first_day
            while day <= last:
                rule = bare.rule_on(day)
                if HabitCheck(rule.check) is HabitCheck.DATA:
                    readings[day] = data.reading(rule, day)
                day += timedelta(days=1)
        facts = HabitFacts(
            first_day=habit.first_day,
            rules=bare.rules,
            marks={mark.day: HabitMarkResult(mark.result) for mark in marks[habit.id]},
            freezes=tuple(shared + own[habit.id]),
            readings=readings,
        )
        out.append(HabitResults(habit, facts, clock, periods(facts, last, clock)))
    return out


def habits_day(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> HabitsDay:
    """The Day tab (brief §7): today's scheduled habits with their results, Morning first, and
    the Monday–Sunday strip of how many were done each day."""
    clock = habit_clock(as_of, now)
    day = clock.today
    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    results = habit_results(session, _active(session), max(sunday, day), clock)
    week = [_count(results, monday + timedelta(days=offset)) for offset in range(7)]
    rows = []
    for item in results:
        result = item.day(day)
        if result.status is DayStatus.NOT_SCHEDULED:
            continue
        rows.append(
            HabitDayRow(
                view=habit_view(session, item.habit, on=day),
                result=result,
                streak=item.streak(),
                progress=item.progress(day),
            )
        )
    count = _count(results, day)
    return HabitsDay(day, day, count.done, count.total, week, rows)


def habits_week(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> HabitsWeek:
    """The Week tab (brief §8): every active habit's Monday–Sunday, with Habits kept for this
    week and the same days of last week."""
    clock = habit_clock(as_of, now)
    monday = clock.today - timedelta(days=clock.today.weekday())
    sunday = monday + timedelta(days=6)
    results = habit_results(session, _active(session), sunday, clock)
    rows = [
        HabitWeekRow(
            view=habit_view(session, item.habit, on=clock.today),
            days=[item.day(monday + timedelta(days=offset)) for offset in range(7)],
            streak=item.streak(),
            progress=item.progress(clock.today),
        )
        for item in results
    ]
    return HabitsWeek(
        as_of=clock.today,
        week_start=monday,
        week_end=sunday,
        rows=rows,
        kept=_kept(results, monday, clock.today),
        kept_last_week=habits_kept(
            session, monday - timedelta(days=7), clock.today - timedelta(days=7), now=now
        ),
    )


def habit_detail(
    session: Session, slug: str, *, as_of: date | None = None, now: datetime | None = None
) -> HabitDetail:
    """One habit's page (brief §8): streaks, Kept last 4 weeks, 12 weeks of history, the last
    14 days, and its freezes (its own and those for all habits)."""
    habit = get_habit(session, slug)
    clock = habit_clock(as_of, now)
    (item,) = habit_results(session, [habit], clock.today, clock)
    since = clock.today - timedelta(days=clock.today.weekday() + 7 * (HISTORY_WEEKS - 1))
    kept, judged = kept_last_4_weeks(item.periods, clock.today)
    recent = [
        item.day(clock.today - timedelta(days=offset))
        for offset in range(RECENT_DAYS)
        if clock.today - timedelta(days=offset) >= habit.first_day
    ]
    return HabitDetail(
        view=habit_view(session, habit, on=clock.today),
        as_of=clock.today,
        current_streak=item.streak(),
        best_streak=best_streak(item.periods),
        kept_last_4_weeks=KeptFigure(kept, judged, share(kept, judged)),
        history=[result for result in item.periods if result.end >= since],
        recent=recent,
        freezes=list_freezes(session, habit_slug=habit.slug),
    )


def habits_kept(
    session: Session, start: date, end: date, *, now: datetime | None = None
) -> KeptFigure:
    """Habits kept across active habits for `start`–`end` (brief §6), as on Home, This week, and
    the Week tab. `end` is judged as "today", so the same days a week earlier compare like for
    like: that week's last day counts only once it is Done, as today does."""
    figures = [figure for _, figure in habits_kept_by_habit(session, start, end, now=now)]
    done = sum(figure.done for figure in figures)
    target = sum(figure.target for figure in figures)
    return KeptFigure(done, target, share(done, target))


def habits_kept_by_habit(
    session: Session, start: date, end: date, *, now: datetime | None = None
) -> list[tuple[Habit, KeptFigure]]:
    """Each active habit's part of Habits kept for `start`–`end`; they add up to the whole."""
    clock = habit_clock(end, now)
    out = []
    for item in habit_results(session, _active(session), end, clock):
        done, target = kept_counts(item.periods, start, end)
        out.append((item.habit, KeptFigure(done, target, share(done, target))))
    return out


def _kept(results: Sequence[HabitResults], start: date, end: date) -> KeptFigure:
    done = target = 0
    for item in results:
        habit_done, habit_target = kept_counts(item.periods, start, end)
        done += habit_done
        target += habit_target
    return KeptFigure(done, target, share(done, target))


def _count(results: Sequence[HabitResults], day: date) -> DayCount:
    days = [item.day(day) for item in results]
    counted = [result for result in days if result.counts]
    return DayCount(day, sum(r.status is DayStatus.DONE for r in counted), len(counted))


def _active(session: Session) -> list[Habit]:
    habits = list_habits(session, include_archived=False)
    order = {value: index for index, value in enumerate(TIME_OF_DAY_ORDER)}
    return sorted(habits, key=lambda habit: (order[TimeOfDay(habit.time_of_day)], habit.name))


def _spec(rule: HabitRule) -> RuleSpec:
    return RuleSpec(
        starts_on=rule.starts_on,
        frequency=rule.frequency,
        check=rule.check,
        weekdays=frozenset(rule.weekdays) if rule.weekdays else None,
        times=rule.times,
        source=rule.source,
        source_ref=rule.source_ref,
        threshold=rule.threshold,
        value=rule.value,
    )


def _by_habit(
    session: Session, model: type[HabitRule] | type[HabitMark], ids: list[int | None], order: Any
) -> dict[int | None, list[Any]]:
    grouped: dict[int | None, list[Any]] = defaultdict(list)
    for row in session.exec(select(model).where(col(model.habit_id).in_(ids)).order_by(order)):
        grouped[row.habit_id].append(row)
    return grouped
