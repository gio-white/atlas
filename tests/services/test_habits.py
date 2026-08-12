from datetime import date

import pytest

from atlas.domain import Aggregation, Comparator, Period, ValueType
from atlas.services import ValidationError, create_habit, create_metric, habit_status
from tests.services.helpers import log_pushups, seed_daily_pushups, seed_health


def test_habit_status_counts_a_daily_streak(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 11))
    log_pushups(session, date(2026, 8, 12))
    log_pushups(session, date(2026, 8, 13))

    status = habit_status(session, "pushups-daily", as_of=date(2026, 8, 13))

    assert status.current_streak == 3
    assert status.longest_streak == 3
    assert status.satisfied is True
    assert status.scheduled is True
    assert status.current_value == 10.0
    assert status.metric_slug == "pushups"


def test_backfilling_an_entry_recomputes_the_streak(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 12))
    log_pushups(session, date(2026, 8, 13))

    before = habit_status(session, "pushups-daily", as_of=date(2026, 8, 13))
    assert before.current_streak == 2

    log_pushups(session, date(2026, 8, 11))

    after = habit_status(session, "pushups-daily", as_of=date(2026, 8, 13))
    assert after.current_streak == 3
    assert after.longest_streak == 3


def test_weekday_mask_skips_off_days(session):
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
    log_pushups(session, date(2026, 8, 10))
    log_pushups(session, date(2026, 8, 11))
    log_pushups(session, date(2026, 8, 12))
    log_pushups(session, date(2026, 8, 13))
    log_pushups(session, date(2026, 8, 14))

    friday = habit_status(session, "weekday-pushups", as_of=date(2026, 8, 14))
    sunday = habit_status(session, "weekday-pushups", as_of=date(2026, 8, 16))

    assert friday.current_streak == 5
    assert sunday.current_streak == 5
    assert sunday.scheduled is False


def test_weekdays_rejected_for_weekly_habits(session):
    seed_health(session)

    with pytest.raises(ValidationError, match="weekdays"):
        create_habit(
            session,
            "weekly",
            metric_slug="pushups",
            period=Period.WEEK,
            target_value=3.0,
            comparator=Comparator.AT_LEAST,
            weekdays=[1, 3, 5],
            active_from=date(2026, 8, 1),
        )


def test_habits_cannot_target_text_metrics(session):
    seed_health(session)
    create_metric(
        session,
        "journal",
        area_slug="health",
        value_type=ValueType.TEXT,
        aggregation=Aggregation.LAST,
    )

    with pytest.raises(ValidationError, match="text metric"):
        create_habit(
            session,
            "journal-daily",
            metric_slug="journal",
            period=Period.DAY,
            target_value=1.0,
            comparator=Comparator.AT_LEAST,
            active_from=date(2026, 8, 1),
        )


def test_in_progress_day_does_not_break_the_streak(session):
    seed_daily_pushups(session)
    log_pushups(session, date(2026, 8, 11))
    log_pushups(session, date(2026, 8, 12))

    status = habit_status(session, "pushups-daily", as_of=date(2026, 8, 13))

    assert status.current_streak == 2
    assert status.satisfied is False
