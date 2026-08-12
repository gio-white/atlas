from datetime import date

from atlas.domain import Comparator, GoalKind, Measure, Period
from atlas.services import (
    area_view,
    create_goal,
    create_habit,
    log_entry,
    today_view,
    week_view,
)
from tests.services.helpers import log_pushups, seed_daily_pushups, seed_health


def test_today_view_shows_due_habits_and_logged_entries(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 13), 40)
    log_entry(session, "meditated", occurred_on=date(2026, 8, 13))

    view = today_view(session, as_of=date(2026, 8, 13))

    assert view.as_of == date(2026, 8, 13)
    assert [habit.slug for habit in view.habits] == ["pushups-daily"]
    assert view.habits[0].satisfied is True
    assert {entry.metric_slug for entry in view.entries} == {"pushups", "meditated"}


def test_today_view_omits_unscheduled_habits(session):
    seed_health(session)
    create_habit(
        session,
        "weekday-pushups",
        metric_slug="pushups",
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        weekdays=[1, 2, 3, 4, 5],
        active_from=date(2026, 8, 10),
    )

    view = today_view(session, as_of=date(2026, 8, 16))

    assert view.habits == []


def test_week_view_covers_the_iso_week(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 10), 10)
    log_pushups(session, date(2026, 8, 12), 20)

    view = week_view(session, as_of=date(2026, 8, 13))

    assert view.week_start == date(2026, 8, 10)
    assert view.week_end == date(2026, 8, 16)
    assert len(view.habits) == 1
    habit = view.habits[0]
    assert len(habit.days) == 7
    by_day = {cell.day: cell for cell in habit.days}
    assert by_day[date(2026, 8, 10)].value == 10.0
    assert by_day[date(2026, 8, 10)].satisfied is True
    assert by_day[date(2026, 8, 11)].value is None
    assert by_day[date(2026, 8, 11)].satisfied is False
    assert by_day[date(2026, 8, 12)].value == 20.0


def test_area_view_groups_metrics_habits_and_goals(session):
    seed_daily_pushups(session)
    create_goal(
        session,
        "bodyweight-75",
        area_slug="health",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
    )
    log_pushups(session, date(2026, 8, 13), 30)
    log_entry(session, "weight", 78.4, occurred_on=date(2026, 8, 13))

    view = area_view(session, "health", as_of=date(2026, 8, 13))

    assert view.slug == "health"
    assert {metric.slug for metric in view.metrics} == {"meditated", "pushups", "weight"}
    weight = next(metric for metric in view.metrics if metric.slug == "weight")
    assert weight.latest_value == 78.4
    assert weight.latest_on == date(2026, 8, 13)
    assert [habit.slug for habit in view.habits] == ["pushups-daily"]
    assert [goal.slug for goal in view.goals] == ["bodyweight-75"]
