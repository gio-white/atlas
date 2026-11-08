from datetime import date

from atlas.domain import Comparator, HabitKind, Period
from atlas.services import (
    archive_metric,
    area_view,
    create_habit,
    habit_calendar,
    log_entry,
)
from tests.services.helpers import log_pushups, seed_daily_pushups, seed_health


def test_habit_calendar_week_covers_the_iso_week(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 10), 10)

    calendar = habit_calendar(session, period=Period.WEEK, as_of=date(2026, 8, 13))

    assert calendar.period is Period.WEEK
    assert calendar.range_start == date(2026, 8, 10)
    assert calendar.range_end == date(2026, 8, 16)
    assert [habit.slug for habit in calendar.habits] == ["pushups-daily"]
    days = calendar.habits[0].days
    assert [cell.day for cell in days] == [date(2026, 8, 10 + offset) for offset in range(7)]
    assert days[0].value == 10.0


def test_habit_calendar_month_spans_the_calendar_month(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 13), 10)

    calendar = habit_calendar(session, period=Period.MONTH, as_of=date(2026, 8, 13))

    assert calendar.range_start == date(2026, 8, 1)
    assert calendar.range_end == date(2026, 8, 31)
    assert len(calendar.habits[0].days) == 31
    by_day = {cell.day: cell for cell in calendar.habits[0].days}
    assert by_day[date(2026, 8, 13)].value == 10.0
    assert by_day[date(2026, 8, 13)].satisfied is True
    assert by_day[date(2026, 8, 14)].satisfied is None


def test_habit_calendar_omits_archived_metric(session):
    seed_daily_pushups(session)
    archive_metric(session, "pushups")

    calendar = habit_calendar(session, period=Period.WEEK, as_of=date(2026, 8, 13))

    assert calendar.habits == []


def test_habit_calendar_day_leaves_weekly_satisfied_open(session):
    seed_health(session)
    create_habit(
        session,
        "pushups-weekly",
        metric_slug="pushups",
        period=Period.WEEK,
        target_value=3.0,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    log_pushups(session, date(2026, 8, 13), 10)

    calendar = habit_calendar(session, period=Period.DAY, as_of=date(2026, 8, 13))

    assert calendar.range_start == calendar.range_end == date(2026, 8, 13)
    assert len(calendar.habits[0].days) == 1
    assert calendar.habits[0].days[0].value == 10.0
    assert calendar.habits[0].days[0].satisfied is None


def test_area_view_groups_metrics_and_habits(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 13), 30)
    log_entry(session, "weight", 78.4, occurred_on=date(2026, 8, 13))

    view = area_view(session, "health", as_of=date(2026, 8, 13))

    assert view.slug == "health"
    assert {metric.slug for metric in view.metrics} == {"meditated", "pushups", "weight"}
    weight = next(metric for metric in view.metrics if metric.slug == "weight")
    assert weight.latest_value == 78.4
    assert weight.latest_on == date(2026, 8, 13)
    assert [habit.slug for habit in view.habits] == ["pushups-daily"]
    assert not hasattr(view, "goals")


def test_habit_calendar_carries_kind_and_weekdays_for_labels(session):
    seed_health(session)
    create_habit(
        session,
        name="Deep work on weekdays",
        kind=HabitKind.DURATION,
        period=Period.DAY,
        target_value=90,
        weekdays=[5, 1, 2, 3, 4],
        active_from=date(2026, 8, 1),
    )

    calendar = habit_calendar(session, period=Period.WEEK, as_of=date(2026, 8, 13))

    habit = calendar.habits[0]
    assert habit.name == "Deep work on weekdays"
    assert habit.kind is HabitKind.DURATION
    assert habit.weekdays == [1, 2, 3, 4, 5]
