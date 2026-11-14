"""Habit calculations (habits brief §2–§6). Pure: no database, no clock.

A habit's facts are its rule versions, your marks, its freezes, and (for a data habit) one
reading per day from its source. Everything here is computed from those facts when a page
loads: the result of each day, the periods with their targets, streaks, "Kept, last 4 weeks",
and Habits kept across habits.

"Today" is the caller's: the local date, or a past *As of* date judged as if that day had just
ended (`Clock.now_minute` is then the whole day).
"""

import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum

from atlas.domain.buckets import bucket_for
from atlas.domain.enums import (
    HabitCheck,
    HabitFrequency,
    HabitMarkResult,
    HabitSource,
    HabitThreshold,
    Period,
)
from atlas.domain.habit_sources import EVENING_SCALE_START, SourceFeed, source_spec

MINUTES_IN_DAY = 24 * 60
KEPT_WINDOW_DAYS = 28


class DayStatus(StrEnum):
    """The result of one day for one habit (brief §6)."""

    NOT_SCHEDULED = "not_scheduled"
    """Before the habit's first day, or not one of its days (a weekday habit on Saturday)."""
    UPCOMING = "upcoming"
    """A scheduled day after today."""
    FROZEN = "frozen"
    DONE = "done"
    NOT_DONE = "not_done"
    OPEN = "open"
    """Today, nothing yet: a manual habit not ticked, a night not arrived, a session not yet
    planned before the cut-off. The brief's In progress without a progress figure."""
    IN_PROGRESS = "in_progress"
    """Today, with progress so far: "20 of 30m", "On track · 40m of 1h 30m"."""
    WAITING = "waiting"
    """Yesterday, for a data habit whose data is not complete yet. It does not break a streak."""
    BLANK = "blank"
    """A past day of a weekly or monthly habit that is not Done: shown blank, never a cross. The
    period's figure carries the judgment (owner, 2026-11-14)."""


class DayReason(StrEnum):
    """The reason line under a day's result (brief §12); the screens word it."""

    NO_DATA = "no_data"
    DATA_INCOMPLETE = "data_incomplete"
    WAITING_FOR_DATA = "waiting_for_data"
    OVER_LIMIT = "over_limit"
    SET_BY_YOU = "set_by_you"
    FROZEN = "frozen"


class PeriodState(StrEnum):
    KEPT = "kept"
    MISSED = "missed"
    RUNNING = "running"
    """Contains today and is not kept yet. Never breaks a streak."""
    WAITING = "waiting"
    """Finished, not kept, and a day in it is still waiting for data."""
    FROZEN = "frozen"
    """No open day: left out entirely."""
    UPCOMING = "upcoming"


@dataclass(frozen=True, slots=True)
class RuleSpec:
    """One rule version, as the calculations see it."""

    starts_on: date
    frequency: HabitFrequency
    check: HabitCheck = HabitCheck.MANUAL
    weekdays: frozenset[int] | None = None
    times: int | None = None
    source: HabitSource | None = None
    source_ref: str | None = None
    """The screen category or app slug a source reads, when it needs one."""
    threshold: HabitThreshold | None = None
    value: float | None = None

    def __post_init__(self) -> None:
        if self.weekdays is not None and not isinstance(self.weekdays, frozenset):
            object.__setattr__(self, "weekdays", frozenset(self.weekdays))

    @property
    def period(self) -> Period:
        return period_of(self.frequency)


@dataclass(frozen=True, slots=True)
class Reading:
    """A data source's value for one day.

    `value` is minutes (time asleep, screen time) or a time of day in minutes after midnight
    (wake time, bedtime, when the first session was planned); None when nothing arrived.
    `complete` says the day's data is final. `received` says some data for the day arrived, so
    an incomplete day reads "Data incomplete" rather than "No data received".
    """

    value: float | None = None
    complete: bool = False
    received: bool = False


NO_READING = Reading()


@dataclass(frozen=True, slots=True)
class HabitFacts:
    """Everything stored about one habit that its results are computed from."""

    first_day: date
    rules: tuple[RuleSpec, ...]
    marks: Mapping[date, HabitMarkResult] = field(default_factory=dict)
    freezes: tuple[tuple[date, date], ...] = ()
    readings: Mapping[date, Reading] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.rules:
            raise ValueError("a habit needs at least one rule version")
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=lambda r: r.starts_on)))
        object.__setattr__(self, "freezes", tuple(self.freezes))

    def rule_on(self, day: date) -> RuleSpec:
        """The version in force on `day`; before the first version, the first one."""
        current = self.rules[0]
        for rule in self.rules:
            if rule.starts_on <= day:
                current = rule
        return current

    def frozen_on(self, day: date) -> bool:
        return any(start <= day <= end for start, end in self.freezes)


@dataclass(frozen=True, slots=True)
class Clock:
    today: date
    now_minute: float = MINUTES_IN_DAY
    """Minutes after local midnight of `today`. A past As of date is the whole day."""

    @property
    def yesterday(self) -> date:
        return self.today - timedelta(days=1)


@dataclass(frozen=True, slots=True)
class DayResult:
    day: date
    status: DayStatus
    reason: DayReason | None = None
    value: float | None = None
    """The day's reading for a data habit (minutes, or a time of day), when there is one."""

    @property
    def counts(self) -> bool:
        """Scheduled and not frozen: the day is in "x of y done"."""
        return self.status not in (
            DayStatus.NOT_SCHEDULED,
            DayStatus.FROZEN,
            DayStatus.UPCOMING,
        )


@dataclass(frozen=True, slots=True)
class PeriodResult:
    period: Period
    start: date
    end: date
    """The period clipped to the habit's days under one kind of rule (see `periods`)."""
    target: int
    done: int
    state: PeriodState
    days: tuple[DayResult, ...]

    def done_through(self, last: date) -> int:
        return sum(1 for day in self.days if day.day <= last and day.status is DayStatus.DONE)


def period_of(frequency: HabitFrequency) -> Period:
    """Every day and Specific days are judged per day; N× a week per week; N× a month per
    calendar month (brief §6)."""
    match HabitFrequency(frequency):
        case HabitFrequency.TIMES_A_WEEK:
            return Period.WEEK
        case HabitFrequency.TIMES_A_MONTH:
            return Period.MONTH
        case _:
            return Period.DAY


def is_due(rule: RuleSpec, day: date) -> bool:
    """Whether the rule asks anything of `day`. A weekly or monthly habit counts every day of its
    period (owner, 2026-11-14)."""
    if HabitFrequency(rule.frequency) is HabitFrequency.SPECIFIC_DAYS:
        return rule.weekdays is not None and day.isoweekday() in rule.weekdays
    return True


def passes(source: HabitSource, threshold: HabitThreshold, value: float, limit: float) -> bool:
    """Whether a reading meets the threshold. Bedtime compares on an evening-to-morning scale
    (18:00 to 17:59), so 00:40 is later than 23:30 (brief §2)."""
    if source_spec(source).evening_scale:
        value = _evening(value)
        limit = _evening(limit)
    match HabitThreshold(threshold):
        case HabitThreshold.AT_LEAST:
            return value >= limit
        case HabitThreshold.AT_MOST:
            return value <= limit
        case HabitThreshold.BEFORE:
            return value < limit
        case HabitThreshold.AFTER:
            return value > limit


def day_result(facts: HabitFacts, day: date, clock: Clock) -> DayResult:
    """The result of one day (brief §3, §4, §6).

    Order: not scheduled; frozen (a freeze wins over a mark, which stays stored); upcoming; your
    mark ("Set by you" on a data habit); then the manual or data rule. A past day of a weekly or
    monthly habit that is not Done is Blank.
    """
    rule = facts.rule_on(day)
    if day < facts.first_day or not is_due(rule, day):
        return DayResult(day, DayStatus.NOT_SCHEDULED)
    if facts.frozen_on(day):
        return DayResult(day, DayStatus.FROZEN, DayReason.FROZEN)
    if day > clock.today:
        return DayResult(day, DayStatus.UPCOMING)
    result = _answer(facts, rule, day, clock)
    if rule.period is not Period.DAY and day < clock.today and result.status is DayStatus.NOT_DONE:
        return DayResult(day, DayStatus.BLANK, result.reason, result.value)
    return result


def periods(facts: HabitFacts, last: date, clock: Clock) -> list[PeriodResult]:
    """Every period from the habit's first day that starts by `last`, oldest first. A period
    that runs past `last` is whole: its later days are upcoming.

    Consecutive rule versions with the same kind of period (day, week, or month) share their
    periods; a weekly or monthly period takes its count from the version in force on its last
    day, so "3× → 4× a week from today" makes the week that contains today a 4× week. Where the
    kind changes (every day → 3× a week), the periods are clipped at the change: the days before
    it are not open for the new rule, so the first period is partial.

    A weekly or monthly target is `ceil(N × open days ÷ days in the period)`, open days being
    the clipped days that are not frozen; a period with no open day is left out (Frozen). The
    first, partial period after the habit's first day follows the same formula (brief §5).
    """
    out: list[PeriodResult] = []
    for kind, start, rule_end in _segments(facts, last):
        if kind is Period.DAY:
            for day in _days(start, min(rule_end or last, last)):
                result = day_result(facts, day, clock)
                if result.status is DayStatus.NOT_SCHEDULED:
                    continue
                target = 0 if result.status is DayStatus.FROZEN else 1
                out.append(_period(kind, day, day, target, (result,), clock))
            continue
        cursor = start
        while cursor <= min(rule_end or last, last):
            # `last` only stops new periods; a period runs to its natural end or the rule change.
            bucket = bucket_for(cursor, kind)
            clip_end = min(bucket.end, rule_end or bucket.end)
            days = tuple(day_result(facts, day, clock) for day in _days(cursor, clip_end))
            length = (bucket.end - bucket.start).days + 1
            open_days = sum(1 for day in days if day.status is not DayStatus.FROZEN)
            times = facts.rule_on(clip_end).times or 0
            target = math.ceil(times * open_days / length) if open_days else 0
            out.append(_period(kind, cursor, clip_end, target, days, clock))
            cursor = clip_end + timedelta(days=1)
    return out


def current_streak(results: Sequence[PeriodResult]) -> int:
    """Consecutive kept periods back from the most recent finished one. Frozen periods, periods
    still waiting for data, and the running period are skipped; the running period adds 1 once
    it is kept (brief §6)."""
    streak = 0
    for result in reversed(results):
        match result.state:
            case PeriodState.KEPT:
                streak += 1
            case PeriodState.MISSED:
                break
    return streak


def best_streak(results: Sequence[PeriodResult]) -> int:
    """The longest run of kept periods ever, by the same rules as the current streak."""
    best = run = 0
    for result in results:
        if result.state is PeriodState.KEPT:
            run += 1
            best = max(best, run)
        elif result.state is PeriodState.MISSED:
            run = 0
    return best


def kept_last_4_weeks(results: Sequence[PeriodResult], today: date) -> tuple[int, int]:
    """(kept, judged) over the periods that ended in the 28 days before today. Frozen, running,
    and waiting periods are not judged."""
    first = today - timedelta(days=KEPT_WINDOW_DAYS)
    judged = [
        result
        for result in results
        if first <= result.end < today and result.state in (PeriodState.KEPT, PeriodState.MISSED)
    ]
    return sum(result.state is PeriodState.KEPT for result in judged), len(judged)


def kept_counts(results: Sequence[PeriodResult], start: date, end: date) -> tuple[int, int]:
    """One habit's share of Habits kept for the days `start`–`end` (brief §6): (done, target).

    A daily habit counts each finished day as a target of 1, and today once it is Done, so the
    morning does not drag the figure down; a frozen, waiting, or upcoming day is left out. A
    weekly or monthly habit counts its whole target for each period that overlaps the days,
    with min(Done, target) where Done counts days up to `end`.
    """
    done = target = 0
    for result in results:
        if result.end < start or result.start > end:
            continue
        if result.period is Period.DAY:
            if result.state is PeriodState.KEPT:
                done += 1
                target += 1
            elif result.state is PeriodState.MISSED:
                target += 1
            continue
        if result.state is PeriodState.UPCOMING:
            continue
        target += result.target
        done += min(result.done_through(end), result.target)
    return done, target


def share(done: int, target: int) -> float | None:
    return None if target == 0 else done / target


def _answer(facts: HabitFacts, rule: RuleSpec, day: date, clock: Clock) -> DayResult:
    mark = facts.marks.get(day)
    manual = HabitCheck(rule.check) is HabitCheck.MANUAL
    if mark is not None:
        status = DayStatus.DONE if mark is HabitMarkResult.DONE else DayStatus.NOT_DONE
        if manual:
            return DayResult(day, status)
        reading = facts.readings.get(day)
        return DayResult(day, status, DayReason.SET_BY_YOU, reading.value if reading else None)
    if manual:
        return DayResult(day, DayStatus.OPEN if day == clock.today else DayStatus.NOT_DONE)
    return _judge(rule, facts.readings.get(day, NO_READING), day, clock)


def _judge(rule: RuleSpec, reading: Reading, day: date, clock: Clock) -> DayResult:
    """A data habit's day from its reading (brief §3, §4).

    Data never counts as success unless it arrived, is complete, and passes. Two shortcuts hold
    because a day's minutes only grow: an "at least" already met is Done, and an "at most"
    already passed is Not done ("Over the limit"), complete or not.
    """
    if rule.source is None or rule.threshold is None or rule.value is None:
        raise ValueError("a data rule needs a source, a threshold, and a value")
    spec = source_spec(rule.source)
    threshold = HabitThreshold(rule.threshold)
    value = reading.value
    today = day == clock.today
    if spec.feed is SourceFeed.SESSIONS:
        if value is not None and value < rule.value:
            return DayResult(day, DayStatus.DONE, value=value)
        if today and clock.now_minute < rule.value:
            return DayResult(day, DayStatus.OPEN)
        return DayResult(day, DayStatus.NOT_DONE)
    if value is not None:
        met = passes(rule.source, threshold, value, rule.value)
        over = threshold is HabitThreshold.AT_MOST and not met
        if reading.complete:
            if met:
                return DayResult(day, DayStatus.DONE, value=value)
            reason = DayReason.OVER_LIMIT if over else None
            return DayResult(day, DayStatus.NOT_DONE, reason, value)
        if threshold is HabitThreshold.AT_LEAST and met:
            return DayResult(day, DayStatus.DONE, value=value)
        if over:
            return DayResult(day, DayStatus.NOT_DONE, DayReason.OVER_LIMIT, value)
    if today:
        if spec.feed is SourceFeed.SCREEN:
            return DayResult(day, DayStatus.IN_PROGRESS, value=value or 0.0)
        return DayResult(day, DayStatus.OPEN)
    if day == clock.yesterday:
        return DayResult(day, DayStatus.WAITING, DayReason.WAITING_FOR_DATA, value)
    reason = DayReason.DATA_INCOMPLETE if reading.received else DayReason.NO_DATA
    return DayResult(day, DayStatus.NOT_DONE, reason, value)


def _period(
    kind: Period,
    start: date,
    end: date,
    target: int,
    days: tuple[DayResult, ...],
    clock: Clock,
) -> PeriodResult:
    done = sum(1 for day in days if day.status is DayStatus.DONE)
    if start > clock.today:
        state = PeriodState.UPCOMING
    elif target == 0:
        state = PeriodState.FROZEN
    elif done >= target:
        state = PeriodState.KEPT
    elif end >= clock.today:
        state = PeriodState.RUNNING
    elif any(day.status is DayStatus.WAITING for day in days):
        state = PeriodState.WAITING
    else:
        state = PeriodState.MISSED
    return PeriodResult(kind, start, end, target, done, state, days)


def _segments(facts: HabitFacts, last: date) -> Iterator[tuple[Period, date, date | None]]:
    """Stretches of days under one kind of period, from the first day: each one's kind, first
    day, and last day before the kind changes (None for the stretch still in force). Stretches
    starting after `last` are left out."""
    if last < facts.first_day:
        return
    bounds: list[tuple[Period, date]] = []
    for index, rule in enumerate(facts.rules):
        # The first version covers everything from the first day (`HabitFacts.rule_on`).
        start = facts.first_day if index == 0 else max(rule.starts_on, facts.first_day)
        if bounds and bounds[-1][1] >= start:
            # Both versions start on the first day: the later one is the one in force.
            bounds[-1] = (rule.period, bounds[-1][1])
            if len(bounds) > 1 and bounds[-2][0] is rule.period:
                bounds.pop()
        elif not bounds or bounds[-1][0] is not rule.period:
            bounds.append((rule.period, start))
    for index, (kind, start) in enumerate(bounds):
        if start > last:
            return
        end = bounds[index + 1][1] - timedelta(days=1) if index + 1 < len(bounds) else None
        yield kind, start, end


def _days(start: date, end: date) -> Iterator[date]:
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def _evening(minute: float) -> float:
    return (minute - EVENING_SCALE_START) % MINUTES_IN_DAY
