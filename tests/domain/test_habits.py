from datetime import date

from atlas.domain import (
    Aggregation,
    Comparator,
    EntryView,
    HabitSpec,
    Period,
    adherence,
    current_streak,
    is_satisfied,
    longest_streak,
    scheduled_buckets,
)

MON, TUE, WED, THU, FRI, SAT, SUN = range(1, 8)
WEEKDAYS = frozenset({MON, TUE, WED, THU, FRI})


def _entry(day: date, value: float = 1.0) -> EntryView:
    return EntryView(occurred_on=day, value_num=value)


def _daily(
    *,
    target_value: float = 1.0,
    comparator: Comparator = Comparator.AT_LEAST,
    aggregation: Aggregation = Aggregation.SUM,
    active_from: date = date(2026, 8, 1),
    active_to: date | None = None,
    weekdays: frozenset[int] | None = None,
    period: Period = Period.DAY,
) -> HabitSpec:
    return HabitSpec(
        period=period,
        target_value=target_value,
        comparator=comparator,
        aggregation=aggregation,
        active_from=active_from,
        active_to=active_to,
        weekdays=weekdays,
    )


def test_empty_bucket_satisfies_at_most_only():
    assert is_satisfied(None, Comparator.AT_MOST, 1.0) is True
    assert is_satisfied(None, Comparator.AT_LEAST, 1.0) is False
    assert is_satisfied(None, Comparator.EXACTLY, 0.0) is False


def test_comparators_against_a_value():
    assert is_satisfied(3.0, Comparator.AT_LEAST, 3.0) is True
    assert is_satisfied(2.0, Comparator.AT_LEAST, 3.0) is False
    assert is_satisfied(1.0, Comparator.AT_MOST, 1.0) is True
    assert is_satisfied(2.0, Comparator.AT_MOST, 1.0) is False
    assert is_satisfied(3.0, Comparator.EXACTLY, 3.0) is True
    assert is_satisfied(3.1, Comparator.EXACTLY, 3.0) is False


def test_coffee_free_day_satisfies_at_most():
    habit = _daily(comparator=Comparator.AT_MOST, target_value=1.0)
    as_of = date(2026, 8, 13)

    assert current_streak(habit, [], as_of) == 13


def test_run_free_week_fails_at_least():
    habit = HabitSpec(
        period=Period.WEEK,
        target_value=3.0,
        comparator=Comparator.AT_LEAST,
        aggregation=Aggregation.SUM,
        active_from=date(2026, 8, 3),
    )
    as_of = date(2026, 8, 16)

    assert current_streak(habit, [], as_of) == 0
    assert longest_streak(habit, [], as_of) == 0


def test_in_progress_unsatisfied_bucket_does_not_break_the_streak():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [_entry(date(2026, 8, d)) for d in (10, 11, 12)]

    assert current_streak(habit, entries, date(2026, 8, 13)) == 3


def test_in_progress_satisfied_bucket_extends_the_streak():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [_entry(date(2026, 8, d)) for d in (10, 11, 12, 13)]

    assert current_streak(habit, entries, date(2026, 8, 13)) == 4


def test_complete_unsatisfied_bucket_breaks_the_streak():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [_entry(date(2026, 8, 10)), _entry(date(2026, 8, 12)), _entry(date(2026, 8, 13))]

    assert current_streak(habit, entries, date(2026, 8, 13)) == 2


def test_weekly_habit_counts_weeks_and_includes_the_open_week_once_met():
    habit = HabitSpec(
        period=Period.WEEK,
        target_value=3.0,
        comparator=Comparator.AT_LEAST,
        aggregation=Aggregation.SUM,
        active_from=date(2026, 7, 13),
    )
    # Four complete ISO weeks before week 33, three runs each, then two so far this week.
    past_weeks = [
        date(2026, 7, 13),
        date(2026, 7, 14),
        date(2026, 7, 15),
        date(2026, 7, 20),
        date(2026, 7, 21),
        date(2026, 7, 22),
        date(2026, 7, 27),
        date(2026, 7, 28),
        date(2026, 7, 29),
        date(2026, 8, 3),
        date(2026, 8, 4),
        date(2026, 8, 5),
    ]
    monday_morning = [_entry(day) for day in past_weeks]
    assert current_streak(habit, monday_morning, date(2026, 8, 10)) == 4

    this_week = monday_morning + [
        _entry(date(2026, 8, 10)),
        _entry(date(2026, 8, 11)),
        _entry(date(2026, 8, 12)),
    ]
    assert current_streak(habit, this_week, date(2026, 8, 13)) == 5


def test_weekday_mask_skips_off_days_without_breaking_the_streak():
    habit = _daily(active_from=date(2026, 8, 10), weekdays=WEEKDAYS)
    entries = [
        _entry(date(2026, 8, 10)),
        _entry(date(2026, 8, 11)),
        _entry(date(2026, 8, 12)),
        _entry(date(2026, 8, 13)),
        _entry(date(2026, 8, 14)),
    ]

    assert current_streak(habit, entries, date(2026, 8, 16)) == 5
    scheduled = scheduled_buckets(habit, date(2026, 8, 16))
    assert [bucket.start.isoweekday() for bucket in scheduled] == [MON, TUE, WED, THU, FRI]


def test_longest_streak_finds_the_best_run_and_ignores_an_open_miss():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [
        _entry(date(2026, 8, 10)),
        _entry(date(2026, 8, 11)),
        _entry(date(2026, 8, 12)),
    ]

    as_of = date(2026, 8, 16)
    assert current_streak(habit, entries, as_of) == 0
    assert longest_streak(habit, entries, as_of) == 3


def test_longest_streak_counts_an_in_progress_hit():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [_entry(date(2026, 8, d)) for d in (10, 11, 12, 13)]

    assert longest_streak(habit, entries, date(2026, 8, 13)) == 4


def test_adherence_excludes_the_in_progress_bucket():
    habit = _daily(active_from=date(2026, 8, 10))
    entries = [_entry(date(2026, 8, 10)), _entry(date(2026, 8, 12))]

    ratio = adherence(habit, entries, date(2026, 8, 10), date(2026, 8, 13))

    assert ratio == 2 / 3


def test_adherence_is_none_when_nothing_complete_was_scheduled():
    habit = _daily(active_from=date(2026, 8, 13))

    assert adherence(habit, [], date(2026, 8, 13), date(2026, 8, 13)) is None


def test_monthly_habit_counts_an_edge_month_once():
    habit = HabitSpec(
        period=Period.MONTH,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        aggregation=Aggregation.SUM,
        active_from=date(2026, 1, 15),
    )
    entries = [
        _entry(date(2026, 1, 20)),
        _entry(date(2026, 2, 1)),
        _entry(date(2026, 3, 10)),
    ]

    assert current_streak(habit, entries, date(2026, 3, 5)) == 2
    assert current_streak(habit, entries, date(2026, 3, 10)) == 3


def test_future_and_inactive_windows_are_not_scheduled():
    habit = _daily(active_from=date(2026, 8, 10), active_to=date(2026, 8, 12))

    assert scheduled_buckets(habit, date(2026, 8, 9)) == []
    days = [bucket.start.day for bucket in scheduled_buckets(habit, date(2026, 8, 20))]
    assert days == [10, 11, 12]
