"""Turn a schema-14 habit into the rebuilt model (habits brief §11). Pure: no database.

Used by the schema 15 migration and by importing an export written before schema 15, so both
give the same result. A habit becomes its first rule version plus the days it was Done; skips
and pauses become freezes elsewhere, one for one.

Only a daily habit on a screen app's minutes can be read from data, so it becomes a data habit
on that app. Everything else is ticked by you (owner, 2026-11-14: anything a device or Atlas
cannot measure is ticked), and its past is kept as one Done mark per day the old rule met:

- check: a day with a yes;
- quit: a day with no slip;
- count or duration, daily: a day whose total met the target (nothing logged counts as 0, so
  an "at most" day with nothing logged is Done);
- count or duration, weekly or monthly "at least": a day with anything logged, so the week is
  kept on that many days (a week of 3 runs needs 3 days with a run);
- weekly or monthly "at most" / "exactly": a day on which the period's running total was still
  within the target. It becomes a daily habit, since "N times" cannot express a ceiling.

Today counts only when the answer is already certain: a tick, or an "at least" already met.
"""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from atlas.domain.buckets import bucket_for
from atlas.domain.enums import (
    Aggregation,
    Comparator,
    HabitCheck,
    HabitFrequency,
    HabitSource,
    HabitThreshold,
    Period,
)
from atlas.domain.models import EntryView
from atlas.domain.rollup import rollup

LEGACY_KINDS = ("check", "count", "duration", "quit")


@dataclass(frozen=True, slots=True)
class LegacyHabit:
    kind: str
    period: Period
    comparator: Comparator
    target_value: float
    active_from: date
    aggregation: Aggregation
    weekdays: frozenset[int] | None = None
    active_to: date | None = None
    breaks: tuple[tuple[date, date], ...] = ()
    screen_app_slug: str | None = None


@dataclass(frozen=True, slots=True)
class RuleShape:
    frequency: HabitFrequency
    check: HabitCheck
    weekdays: tuple[int, ...] | None = None
    times: int | None = None
    source: HabitSource | None = None
    source_ref: str | None = None
    threshold: HabitThreshold | None = None
    value: float | None = None


@dataclass(frozen=True, slots=True)
class ConvertedHabit:
    rule: RuleShape
    done_days: tuple[date, ...]


def convert_legacy_habit(
    habit: LegacyHabit, entries: Sequence[EntryView], today: date
) -> ConvertedHabit:
    kind = habit.kind.lower()
    if kind not in LEGACY_KINDS:
        raise ValueError(f"unknown habit kind {habit.kind!r}")
    weekdays = tuple(sorted(habit.weekdays)) if habit.weekdays else None
    if _reads_screen_app(habit):
        return ConvertedHabit(
            rule=RuleShape(
                frequency=_daily_frequency(weekdays),
                weekdays=weekdays,
                check=HabitCheck.DATA,
                source=HabitSource.SCREEN_APP,
                source_ref=habit.screen_app_slug,
                threshold=(
                    HabitThreshold.AT_LEAST
                    if habit.comparator is Comparator.AT_LEAST
                    else HabitThreshold.AT_MOST
                ),
                value=habit.target_value,
            ),
            done_days=(),
        )
    rule = _manual_rule(habit, kind, weekdays)
    return ConvertedHabit(rule=rule, done_days=_done_days(habit, kind, rule, entries, today))


def _reads_screen_app(habit: LegacyHabit) -> bool:
    return (
        habit.screen_app_slug is not None
        and habit.period is Period.DAY
        and habit.comparator in (Comparator.AT_LEAST, Comparator.AT_MOST)
        and habit.kind.lower() != "quit"
    )


def _daily_frequency(weekdays: tuple[int, ...] | None) -> HabitFrequency:
    return HabitFrequency.SPECIFIC_DAYS if weekdays else HabitFrequency.EVERY_DAY


def _manual_rule(habit: LegacyHabit, kind: str, weekdays: tuple[int, ...] | None) -> RuleShape:
    if kind == "quit" or habit.period is Period.DAY:
        if kind == "quit":
            weekdays = None
        return RuleShape(
            frequency=_daily_frequency(weekdays), weekdays=weekdays, check=HabitCheck.MANUAL
        )
    if habit.comparator is not Comparator.AT_LEAST:
        return RuleShape(frequency=HabitFrequency.EVERY_DAY, check=HabitCheck.MANUAL)
    most = 7 if habit.period is Period.WEEK else 31
    times = min(most, max(1, math.ceil(habit.target_value)))
    frequency = (
        HabitFrequency.TIMES_A_WEEK if habit.period is Period.WEEK else HabitFrequency.TIMES_A_MONTH
    )
    return RuleShape(frequency=frequency, times=times, check=HabitCheck.MANUAL)


def _done_days(
    habit: LegacyHabit,
    kind: str,
    rule: RuleShape,
    entries: Sequence[EntryView],
    today: date,
) -> tuple[date, ...]:
    by_day: dict[date, list[EntryView]] = defaultdict(list)
    for entry in entries:
        by_day[entry.occurred_on].append(entry)
    last = today if habit.active_to is None else min(today, habit.active_to)
    running_ceiling = rule.frequency is HabitFrequency.EVERY_DAY and habit.period is not Period.DAY
    period_totals: dict[object, float] = defaultdict(float)
    done: list[date] = []
    day = habit.active_from
    while day <= last:
        value = rollup(by_day.get(day, []), habit.aggregation)
        if running_ceiling:
            key = bucket_for(day, habit.period).key
            period_totals[key] += value or 0.0
        if _scheduled(rule, day) and not _on_break(habit, day):
            is_today = day == today
            if running_ceiling:
                met = _within(period_totals[key], habit) and not is_today
            else:
                met = _day_met(habit, kind, value, is_today)
            if met:
                done.append(day)
        day += timedelta(days=1)
    return tuple(done)


def _day_met(habit: LegacyHabit, kind: str, value: float | None, is_today: bool) -> bool:
    if kind == "check":
        return (value or 0.0) > 0
    if kind == "quit":
        return not is_today and (value or 0.0) <= 0
    if habit.period is not Period.DAY:
        return (value or 0.0) > 0
    if habit.comparator is Comparator.AT_LEAST:
        return value is not None and value >= habit.target_value
    return not is_today and _within(value or 0.0, habit)


def _within(total: float, habit: LegacyHabit) -> bool:
    if habit.comparator is Comparator.EXACTLY:
        return total == habit.target_value
    return total <= habit.target_value


def _scheduled(rule: RuleShape, day: date) -> bool:
    return rule.weekdays is None or day.isoweekday() in rule.weekdays


def _on_break(habit: LegacyHabit, day: date) -> bool:
    return any(start <= day <= end for start, end in habit.breaks)
