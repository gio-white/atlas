from datetime import date, timedelta

import pytest

from atlas.domain import (
    Aggregation,
    Comparator,
    HabitCheck,
    HabitFrequency,
    HabitSource,
    HabitThreshold,
    Period,
)
from atlas.domain.habit_migration import LegacyHabit, convert_legacy_habit
from atlas.domain.models import EntryView

MONDAY = date(2026, 8, 10)
TODAY = MONDAY + timedelta(days=13)  # Sunday, two weeks later


def _habit(kind: str = "count", **fields) -> LegacyHabit:
    defaults = {
        "period": Period.DAY,
        "comparator": Comparator.AT_LEAST,
        "target_value": 1.0,
        "active_from": MONDAY,
        "aggregation": Aggregation.SUM,
    }
    return LegacyHabit(kind=kind, **{**defaults, **fields})


def _num(offset: int, value: float) -> EntryView:
    return EntryView(occurred_on=MONDAY + timedelta(days=offset), value_num=value)


def _days(*offsets: int) -> tuple[date, ...]:
    return tuple(MONDAY + timedelta(days=offset) for offset in offsets)


def test_a_check_habit_is_done_on_each_day_with_a_yes():
    entries = [EntryView(occurred_on=MONDAY, value_bool=True), _num(2, 1)]

    result = convert_legacy_habit(_habit("check"), entries, TODAY)

    assert result.rule.frequency is HabitFrequency.EVERY_DAY
    assert result.rule.check is HabitCheck.MANUAL
    assert result.done_days == _days(0, 2)


def test_a_daily_target_is_done_only_where_it_was_met():
    habit = _habit(target_value=30.0, weekdays=frozenset({1, 2, 3, 4, 5}))
    entries = [_num(0, 40), _num(1, 10), _num(5, 50)]  # the Saturday is unscheduled

    result = convert_legacy_habit(habit, entries, TODAY)

    assert result.rule.frequency is HabitFrequency.SPECIFIC_DAYS
    assert result.rule.weekdays == (1, 2, 3, 4, 5)
    assert result.done_days == _days(0)


def test_a_daily_ceiling_counts_an_empty_day_as_done_but_not_today():
    habit = _habit(comparator=Comparator.AT_MOST, target_value=1.0)
    entries = [_num(offset, 2) for offset in range(1, 14)]
    entries.append(_num(13, -2))  # today nets to zero, still not certain

    result = convert_legacy_habit(habit, entries, TODAY)

    assert result.done_days == _days(0)


def test_a_quit_habit_is_done_on_days_without_a_slip_and_ignores_weekdays():
    habit = _habit(
        "quit",
        comparator=Comparator.AT_MOST,
        target_value=0.0,
        weekdays=frozenset({1}),
        active_to=MONDAY + timedelta(days=3),
    )

    result = convert_legacy_habit(habit, [_num(1, 1)], TODAY)

    assert result.rule.frequency is HabitFrequency.EVERY_DAY
    assert result.rule.weekdays is None
    assert result.done_days == _days(0, 2, 3)


@pytest.mark.parametrize(
    ("period", "target", "frequency", "times"),
    [
        (Period.WEEK, 3.0, HabitFrequency.TIMES_A_WEEK, 3),
        (Period.WEEK, 2.5, HabitFrequency.TIMES_A_WEEK, 3),
        (Period.WEEK, 20.0, HabitFrequency.TIMES_A_WEEK, 7),
        (Period.MONTH, 0.0, HabitFrequency.TIMES_A_MONTH, 1),
    ],
)
def test_a_weekly_or_monthly_minimum_becomes_n_times(period, target, frequency, times):
    result = convert_legacy_habit(_habit(period=period, target_value=target), [], TODAY)
    assert (result.rule.frequency, result.rule.times) == (frequency, times)


def test_a_weekly_minimum_is_done_on_each_day_with_activity():
    habit = _habit(period=Period.WEEK, target_value=3.0)
    result = convert_legacy_habit(habit, [_num(0, 1), _num(2, 5), _num(8, 1)], TODAY)
    assert result.done_days == _days(0, 2, 8)


def test_a_weekly_ceiling_is_done_while_the_running_total_stays_within_it():
    habit = _habit(period=Period.WEEK, comparator=Comparator.AT_MOST, target_value=3.0)
    entries = [_num(0, 2), _num(2, 2), _num(7, 1)]

    result = convert_legacy_habit(habit, entries, TODAY)

    assert result.rule.frequency is HabitFrequency.EVERY_DAY
    assert result.rule.times is None
    # Week one: within 3 on Mon-Tue, over from Wednesday. Week two: within, except today.
    assert result.done_days == _days(0, 1, 7, 8, 9, 10, 11, 12)


def test_breaks_leave_no_done_days():
    habit = _habit("check", breaks=((MONDAY, MONDAY + timedelta(days=1)),))
    entries = [EntryView(occurred_on=MONDAY + timedelta(days=d), value_bool=True) for d in (0, 2)]
    assert convert_legacy_habit(habit, entries, TODAY).done_days == _days(2)


def test_a_daily_screen_app_habit_becomes_a_data_habit_with_no_marks():
    habit = _habit(
        "duration",
        comparator=Comparator.AT_MOST,
        target_value=30.0,
        screen_app_slug="instagram",
    )

    result = convert_legacy_habit(habit, [_num(0, 10)], TODAY)

    assert result.rule.check is HabitCheck.DATA
    assert result.rule.source is HabitSource.SCREEN_APP
    assert result.rule.source_ref == "instagram"
    assert (result.rule.threshold, result.rule.value) == (HabitThreshold.AT_MOST, 30.0)
    assert result.done_days == ()


def test_a_weekly_screen_app_habit_stays_manual():
    habit = _habit(period=Period.WEEK, target_value=2.0, screen_app_slug="instagram")
    assert convert_legacy_habit(habit, [], TODAY).rule.check is HabitCheck.MANUAL


def test_an_unknown_kind_is_refused():
    with pytest.raises(ValueError, match="unknown habit kind"):
        convert_legacy_habit(_habit("streak"), [], TODAY)
