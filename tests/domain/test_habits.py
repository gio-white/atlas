"""Habit calculations (habits brief §6): every case the brief lists, plus streaks and kept."""

from datetime import date, timedelta

from atlas.domain.enums import (
    HabitCheck,
    HabitFrequency,
    HabitMarkResult,
    HabitSource,
    HabitThreshold,
    Period,
)
from atlas.domain.habits import (
    Clock,
    DayReason,
    DayStatus,
    HabitFacts,
    PeriodState,
    Reading,
    RuleSpec,
    best_streak,
    current_streak,
    day_result,
    kept_counts,
    kept_last_4_weeks,
    passes,
    periods,
    share,
)

MON = date(2026, 11, 9)
SAT = date(2026, 11, 14)
DONE = HabitMarkResult.DONE
NOT_DONE = HabitMarkResult.NOT_DONE


def _day(offset: int) -> date:
    return MON + timedelta(days=offset)


def _manual(starts_on: date = MON, frequency=HabitFrequency.EVERY_DAY, **values) -> RuleSpec:
    return RuleSpec(starts_on=starts_on, frequency=frequency, **values)


def _data(
    source: HabitSource,
    threshold: HabitThreshold,
    value: float,
    starts_on: date = MON,
    frequency=HabitFrequency.EVERY_DAY,
    **values,
) -> RuleSpec:
    return RuleSpec(
        starts_on=starts_on,
        frequency=frequency,
        check=HabitCheck.DATA,
        source=source,
        threshold=threshold,
        value=value,
        **values,
    )


def _facts(*rules: RuleSpec, first_day: date = MON, **values) -> HabitFacts:
    return HabitFacts(first_day=first_day, rules=rules, **values)


def _status(facts: HabitFacts, day: date, today: date = SAT, now: float = 12 * 60):
    result = day_result(facts, day, Clock(today, now))
    return result.status, result.reason


WAKE_BEFORE_7 = _data(HabitSource.WAKE_TIME, HabitThreshold.BEFORE, 7 * 60)
BAD_AT_MOST_90 = _data(HabitSource.SCREEN_BAD_APPS, HabitThreshold.AT_MOST, 90)
SCREEN_AT_LEAST_30 = _data(HabitSource.SCREEN_APP, HabitThreshold.AT_LEAST, 30)
PLANNED_BEFORE_NOON = _data(HabitSource.SESSIONS_PLANNED, HabitThreshold.BEFORE, 12 * 60)


# A manual tick and its removal.


def test_a_tick_is_done_and_removing_it_makes_the_day_not_done():
    ticked = _facts(_manual(), marks={_day(2): DONE})
    assert _status(ticked, _day(2)) == (DayStatus.DONE, None)
    unticked = _facts(_manual())
    assert _status(unticked, _day(2)) == (DayStatus.NOT_DONE, None)


def test_a_manual_habit_is_open_today_until_ticked():
    assert _status(_facts(_manual()), SAT) == (DayStatus.OPEN, None)
    assert _status(_facts(_manual(), marks={SAT: DONE}), SAT) == (DayStatus.DONE, None)


def test_days_before_the_first_day_and_off_days_are_not_scheduled():
    weekdays = _manual(frequency=HabitFrequency.SPECIFIC_DAYS, weekdays=frozenset({1, 2, 3, 4, 5}))
    facts = _facts(weekdays)
    assert _status(facts, _day(-1))[0] is DayStatus.NOT_SCHEDULED
    assert _status(facts, SAT)[0] is DayStatus.NOT_SCHEDULED
    assert _status(facts, _day(4))[0] is DayStatus.NOT_DONE


def test_a_day_after_today_is_upcoming():
    assert _status(_facts(_manual()), _day(6))[0] is DayStatus.UPCOMING


# An override beats the data, both ways.


def test_your_answer_beats_the_data_both_ways():
    early = {_day(2): Reading(6 * 60 + 30, complete=True, received=True)}
    late = {_day(3): Reading(8 * 60, complete=True, received=True)}
    facts = _facts(
        WAKE_BEFORE_7,
        readings={**early, **late},
        marks={_day(2): NOT_DONE, _day(3): DONE},
    )
    assert _status(facts, _day(2)) == (DayStatus.NOT_DONE, DayReason.SET_BY_YOU)
    assert _status(facts, _day(3)) == (DayStatus.DONE, DayReason.SET_BY_YOU)
    plain = _facts(WAKE_BEFORE_7, readings={**early, **late})
    assert _status(plain, _day(2)) == (DayStatus.DONE, None)
    assert _status(plain, _day(3)) == (DayStatus.NOT_DONE, None)


def test_a_done_data_day_carries_its_value_for_the_reason_line():
    facts = _facts(WAKE_BEFORE_7, readings={_day(2): Reading(408, complete=True, received=True)})
    assert day_result(facts, _day(2), Clock(SAT)).value == 408


# Missing and incomplete data.


def test_no_night_is_not_done_with_no_data_received():
    assert _status(_facts(WAKE_BEFORE_7), _day(2)) == (DayStatus.NOT_DONE, DayReason.NO_DATA)


def test_an_incomplete_screen_time_day_is_not_done_with_data_incomplete():
    partial = Reading(30, complete=False, received=True)
    facts = _facts(BAD_AT_MOST_90, readings={_day(2): partial})
    assert _status(facts, _day(2)) == (DayStatus.NOT_DONE, DayReason.DATA_INCOMPLETE)
    nothing = _facts(BAD_AT_MOST_90)
    assert _status(nothing, _day(2)) == (DayStatus.NOT_DONE, DayReason.NO_DATA)
    complete = _facts(BAD_AT_MOST_90, readings={_day(2): Reading(30, True, True)})
    assert _status(complete, _day(2)) == (DayStatus.DONE, None)


def test_a_complete_day_with_no_screen_time_is_done_under_a_limit():
    facts = _facts(BAD_AT_MOST_90, readings={_day(2): Reading(0.0, True, True)})
    assert _status(facts, _day(2)) == (DayStatus.DONE, None)


def test_an_at_least_already_met_is_done_before_the_data_is_complete():
    facts = _facts(SCREEN_AT_LEAST_30, readings={_day(2): Reading(45, False, True)})
    assert _status(facts, _day(2)) == (DayStatus.DONE, None)


# While the day is running.


def test_going_over_the_limit_mid_day_is_not_done_at_once():
    on_track = _facts(BAD_AT_MOST_90, readings={SAT: Reading(40, False, True)})
    result = day_result(on_track, SAT, Clock(SAT, 15 * 60))
    assert (result.status, result.value) == (DayStatus.IN_PROGRESS, 40)
    over = _facts(BAD_AT_MOST_90, readings={SAT: Reading(95, False, True)})
    assert _status(over, SAT) == (DayStatus.NOT_DONE, DayReason.OVER_LIMIT)


def test_an_at_least_in_progress_today_shows_progress_then_done():
    facts = _facts(SCREEN_AT_LEAST_30, readings={SAT: Reading(20, False, True)})
    result = day_result(facts, SAT, Clock(SAT, 15 * 60))
    assert (result.status, result.value) == (DayStatus.IN_PROGRESS, 20)
    met = _facts(SCREEN_AT_LEAST_30, readings={SAT: Reading(30, False, True)})
    assert _status(met, SAT) == (DayStatus.DONE, None)


def test_a_time_threshold_shows_nothing_today_until_the_value_arrives():
    assert _status(_facts(WAKE_BEFORE_7), SAT) == (DayStatus.OPEN, None)
    arrived = _facts(WAKE_BEFORE_7, readings={SAT: Reading(6 * 60, True, True)})
    assert _status(arrived, SAT) == (DayStatus.DONE, None)


def test_yesterday_waits_for_data_and_is_not_done_once_today_ends():
    facts = _facts(BAD_AT_MOST_90, readings={_day(4): Reading(30, False, True)})
    friday = _day(4)
    assert _status(facts, friday, today=SAT) == (DayStatus.WAITING, DayReason.WAITING_FOR_DATA)
    sunday = _day(6)
    assert _status(facts, friday, today=sunday) == (DayStatus.NOT_DONE, DayReason.DATA_INCOMPLETE)


def test_late_data_re_judges_the_day():
    sunday = _day(6)
    before = _facts(BAD_AT_MOST_90)
    assert _status(before, _day(4), today=sunday) == (DayStatus.NOT_DONE, DayReason.NO_DATA)
    late = _facts(BAD_AT_MOST_90, readings={_day(4): Reading(60, True, True)})
    assert _status(late, _day(4), today=sunday) == (DayStatus.DONE, None)


def test_yesterday_waiting_does_not_break_the_streak():
    readings = {_day(offset): Reading(30, True, True) for offset in range(4)}
    facts = _facts(BAD_AT_MOST_90, readings=readings)
    results = periods(facts, SAT, Clock(SAT))
    assert [result.state for result in results][-2:] == [PeriodState.WAITING, PeriodState.RUNNING]
    assert current_streak(results) == 4


# Bedtime and Sessions planned.


def test_a_bedtime_after_midnight_is_later_than_one_before_it():
    assert passes(HabitSource.BEDTIME, HabitThreshold.BEFORE, 23 * 60 + 30, 23 * 60 + 45)
    assert not passes(HabitSource.BEDTIME, HabitThreshold.BEFORE, 40, 23 * 60 + 30)
    assert passes(HabitSource.BEDTIME, HabitThreshold.AFTER, 40, 23 * 60 + 30)
    assert passes(HabitSource.WAKE_TIME, HabitThreshold.BEFORE, 6 * 60 + 48, 7 * 60)


def test_sessions_planned_turns_done_before_the_cut_off_and_not_done_after_it():
    planned = _facts(PLANNED_BEFORE_NOON, readings={SAT: Reading(8 * 60 + 10, True, True)})
    result = day_result(planned, SAT, Clock(SAT, 8 * 60 + 15))
    assert (result.status, result.value) == (DayStatus.DONE, 8 * 60 + 10)
    nothing = _facts(PLANNED_BEFORE_NOON)
    assert _status(nothing, SAT, now=11 * 60 + 59) == (DayStatus.OPEN, None)
    assert _status(nothing, SAT, now=12 * 60) == (DayStatus.NOT_DONE, None)
    too_late = _facts(PLANNED_BEFORE_NOON, readings={SAT: Reading(12 * 60 + 5, True, True)})
    assert _status(too_late, SAT, now=13 * 60) == (DayStatus.NOT_DONE, None)


def test_a_session_planned_the_day_before_counts():
    facts = _facts(PLANNED_BEFORE_NOON, readings={_day(2): Reading(-120, True, True)})
    assert _status(facts, _day(2)) == (DayStatus.DONE, None)


# Rule changes.


def test_a_threshold_change_from_today_keeps_past_results():
    readings = {_day(offset): Reading(7 * 60 + 15, True, True) for offset in range(6)}
    later = _data(HabitSource.WAKE_TIME, HabitThreshold.BEFORE, 7 * 60 + 30, starts_on=SAT)
    from_today = _facts(WAKE_BEFORE_7, later, readings=readings)
    assert _status(from_today, _day(3)) == (DayStatus.NOT_DONE, None)
    assert _status(from_today, SAT) == (DayStatus.DONE, None)
    all_days = _facts(
        _data(HabitSource.WAKE_TIME, HabitThreshold.BEFORE, 7 * 60 + 30), readings=readings
    )
    assert _status(all_days, _day(3)) == (DayStatus.DONE, None)


def test_a_count_change_applies_to_the_whole_week_that_contains_it():
    three = _manual(frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    four = _manual(starts_on=_day(3), frequency=HabitFrequency.TIMES_A_WEEK, times=4)
    facts = _facts(three, four, first_day=_day(-7))
    first, second = periods(facts, SAT, Clock(SAT))
    assert (first.target, second.target) == (3, 4)
    assert (second.start, second.end) == (MON, _day(6))


def test_every_day_to_three_a_week_starts_a_partial_week():
    daily = _manual()
    weekly = _manual(starts_on=_day(3), frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    facts = _facts(daily, weekly, marks={_day(0): DONE, _day(1): DONE, _day(2): DONE})
    results = periods(facts, _day(6), Clock(_day(6)))
    assert [result.period for result in results] == [Period.DAY] * 3 + [Period.WEEK]
    partial = results[-1]
    assert (partial.start, partial.end, partial.target) == (_day(3), _day(6), 2)


# Freezes.


def test_a_single_day_freeze_neither_breaks_nor_counts():
    marks = {_day(offset): DONE for offset in (0, 1, 3, 4)}
    facts = _facts(_manual(), marks=marks, freezes=((_day(2), _day(2)),))
    assert _status(facts, _day(2)) == (DayStatus.FROZEN, DayReason.FROZEN)
    results = periods(facts, _day(4), Clock(_day(5)))
    assert current_streak(results) == 4
    assert kept_counts(results, MON, _day(4)) == (4, 4)


def test_a_holiday_freeze_leaves_the_streak_intact():
    marks = {_day(offset): DONE for offset in range(-3, 0)}
    marks[_day(5)] = DONE
    facts = _facts(_manual(), first_day=_day(-3), marks=marks, freezes=((MON, _day(4)),))
    results = periods(facts, SAT, Clock(SAT))
    assert current_streak(results) == 4
    assert best_streak(results) == 4


def test_a_freeze_wins_over_a_tick_on_the_same_day():
    facts = _facts(_manual(), marks={_day(2): DONE}, freezes=((_day(2), _day(2)),))
    assert _status(facts, _day(2))[0] is DayStatus.FROZEN


def test_a_week_fully_frozen_is_left_out():
    weekly = _manual(frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    facts = _facts(weekly, freezes=((MON, _day(6)),))
    (week,) = periods(facts, _day(6), Clock(_day(7)))
    assert (week.target, week.state) == (0, PeriodState.FROZEN)


# Proportional weekly targets.


def test_a_partly_frozen_week_scales_its_target():
    weekly = _manual(frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    facts = _facts(weekly, freezes=((MON, _day(2)),), marks={_day(4): DONE, _day(5): DONE})
    (week,) = periods(facts, _day(6), Clock(_day(7)))
    assert (week.target, week.done, week.state) == (2, 2, PeriodState.KEPT)


def test_a_habit_created_mid_week_has_a_partial_first_week():
    weekly = _manual(starts_on=_day(3), frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    facts = _facts(weekly, first_day=_day(3))
    (week,) = periods(facts, _day(6), Clock(_day(7)))
    assert (week.start, week.target) == (_day(3), 2)


def test_a_monthly_habit_counts_calendar_months():
    monthly = _manual(starts_on=date(2026, 10, 1), frequency=HabitFrequency.TIMES_A_MONTH, times=2)
    facts = _facts(monthly, first_day=date(2026, 10, 1), marks={date(2026, 10, 5): DONE})
    october, november = periods(facts, SAT, Clock(SAT))
    assert (october.target, october.state) == (2, PeriodState.MISSED)
    assert (november.start, november.end, november.target, november.state) == (
        date(2026, 11, 1),
        date(2026, 11, 30),
        2,
        PeriodState.RUNNING,
    )


def test_a_weekly_habit_shows_past_days_without_a_tick_as_blank():
    weekly = _manual(frequency=HabitFrequency.TIMES_A_WEEK, times=2)
    facts = _facts(weekly, marks={_day(1): DONE})
    assert _status(facts, _day(0))[0] is DayStatus.BLANK
    assert _status(facts, _day(1))[0] is DayStatus.DONE
    assert _status(facts, SAT)[0] is DayStatus.OPEN


# Streaks and Kept, last 4 weeks.


def test_the_running_period_adds_one_once_kept_and_never_breaks():
    marks = {_day(offset): DONE for offset in range(5)}
    facts = _facts(_manual(), marks=marks)
    assert current_streak(periods(facts, SAT, Clock(SAT))) == 5
    marks[SAT] = DONE
    facts = _facts(_manual(), marks=marks)
    assert current_streak(periods(facts, SAT, Clock(SAT))) == 6


def test_a_missed_day_breaks_the_current_streak_but_not_the_best():
    marks = {_day(offset): DONE for offset in (0, 1, 2, 4)}
    results = periods(_facts(_manual(), marks=marks), _day(5), Clock(_day(5)))
    assert current_streak(results) == 1
    assert best_streak(results) == 3


def test_a_weekly_streak_counts_weeks():
    weekly = _manual(starts_on=_day(-21), frequency=HabitFrequency.TIMES_A_WEEK, times=2)
    marks = {_day(offset): DONE for offset in (-21, -20, -14, -13, -7, -6)}
    results = periods(_facts(weekly, first_day=_day(-21), marks=marks), SAT, Clock(SAT))
    assert current_streak(results) == 3
    marks.update({MON: DONE, _day(1): DONE})
    results = periods(_facts(weekly, first_day=_day(-21), marks=marks), SAT, Clock(SAT))
    assert current_streak(results) == 4


def test_kept_last_4_weeks_judges_finished_periods_in_the_28_days_before_today():
    first = SAT - timedelta(days=40)
    marks = {first + timedelta(days=offset): DONE for offset in range(0, 41, 2)}
    results = periods(
        _facts(_manual(starts_on=first), first_day=first, marks=marks), SAT, Clock(SAT)
    )
    kept, judged = kept_last_4_weeks(results, SAT)
    assert judged == 28
    assert kept == sum(1 for offset in range(12, 40) if offset % 2 == 0)


def test_kept_last_4_weeks_leaves_out_frozen_running_and_waiting_periods():
    facts = _facts(
        BAD_AT_MOST_90,
        readings={_day(0): Reading(30, True, True)},
        freezes=((_day(1), _day(2)),),
    )
    results = periods(facts, SAT, Clock(SAT))
    # Monday kept, Thursday missed (no data); Tue–Wed frozen, Friday waiting, today running.
    assert kept_last_4_weeks(results, SAT) == (1, 2)


# Habits kept.


def test_habits_kept_counts_finished_days_and_today_once_done():
    marks = {_day(offset): DONE for offset in (0, 1, 3)}
    daily = periods(_facts(_manual(), marks=marks), _day(6), Clock(_day(4)))
    assert kept_counts(daily, MON, _day(6)) == (3, 4)
    marks[_day(4)] = DONE
    daily = periods(_facts(_manual(), marks=marks), _day(6), Clock(_day(4)))
    assert kept_counts(daily, MON, _day(6)) == (4, 5)


def test_habits_kept_takes_min_of_done_and_the_whole_weekly_target():
    weekly = _manual(frequency=HabitFrequency.TIMES_A_WEEK, times=2)
    marks = {_day(offset): DONE for offset in (0, 1, 2)}
    results = periods(_facts(weekly, marks=marks), _day(6), Clock(_day(3)))
    assert kept_counts(results, MON, _day(6)) == (2, 2)
    one = periods(_facts(weekly, marks={MON: DONE}), _day(6), Clock(_day(3)))
    assert kept_counts(one, MON, _day(6)) == (1, 2)
    assert share(3, 4) == 0.75
    assert share(0, 0) is None
