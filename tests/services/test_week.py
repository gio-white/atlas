from datetime import UTC, date, datetime, timedelta

import pytest

from atlas.domain import (
    Comparator,
    HabitKind,
    LibraryKind,
    LibraryStatus,
    Period,
    ScreenJudgment,
    TaskStatus,
)
from atlas.domain.quests import QuestKind
from atlas.services import (
    create_habit,
    create_library_title,
    create_screen_app,
    create_screen_category,
    log_entry,
    log_screen_session,
    log_sleep_session,
    this_week,
    week_so_far,
)
from atlas.services.quests import complete_container, create_container, create_task, update_task
from atlas.services.time_blocks import (
    cancel_time_block,
    complete_time_block,
    create_time_block,
    miss_time_block,
)

# Thursday 13 Aug 2026, 18:00 UTC; the week started on Monday 10 Aug.
NOW = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
TODAY = date(2026, 8, 13)


@pytest.fixture(autouse=True)
def utc_zone(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def _session_at(session, task_id: int, start: datetime):
    return create_time_block(
        session, task_id=task_id, start_at=start, end_at=start + timedelta(hours=1), now=NOW
    )


def test_an_empty_database_has_nothing_to_report(session):
    week = week_so_far(session, as_of=TODAY, now=NOW)

    assert week.week_start == date(2026, 8, 10)
    assert (week.sessions_kept, week.sessions_total) == (0, 0)
    assert week.habits_kept_share is None
    assert week.sleep_average_minutes is None
    assert week.sleep_nights == 0
    assert week.screen_score is None


def test_sessions_kept_this_week(session):
    task = create_task(session, title="Study", standalone=True, now=NOW)
    done = _session_at(session, task.id, datetime(2026, 8, 10, 9, tzinfo=UTC))
    missed = _session_at(session, task.id, datetime(2026, 8, 11, 9, tzinfo=UTC))
    _session_at(session, task.id, datetime(2026, 8, 12, 9, tzinfo=UTC))  # unconfirmed
    cancelled = _session_at(session, task.id, datetime(2026, 8, 12, 14, tzinfo=UTC))
    _session_at(session, task.id, datetime(2026, 8, 13, 20, tzinfo=UTC))  # later today
    last_week = _session_at(session, task.id, datetime(2026, 8, 7, 9, tzinfo=UTC))
    complete_time_block(session, done.id, now=NOW)
    complete_time_block(session, last_week.id, now=NOW)
    miss_time_block(session, missed.id, now=NOW)
    cancel_time_block(session, cancelled.id, now=NOW)

    week = week_so_far(session, as_of=TODAY, now=NOW)

    assert (week.sessions_kept, week.sessions_total) == (1, 3)


def test_looking_back_at_a_past_day_only_counts_answers_due_by_then(session):
    task = create_task(session, title="Study", standalone=True, now=NOW)
    _session_at(session, task.id, datetime(2026, 8, 10, 9, tzinfo=UTC))
    _session_at(session, task.id, datetime(2026, 8, 12, 9, tzinfo=UTC))

    monday = week_so_far(session, as_of=date(2026, 8, 10), now=NOW)

    assert monday.week_start == date(2026, 8, 10)
    assert (monday.sessions_kept, monday.sessions_total) == (0, 1)


def test_habits_kept_reuses_adherence_and_leaves_today_open(session):
    create_habit(
        session,
        name="Read",
        kind=HabitKind.CHECK,
        period=Period.DAY,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    for day in (date(2026, 8, 10), date(2026, 8, 12), TODAY):
        log_entry(session, "read", True, occurred_on=day)

    week = week_so_far(session, as_of=TODAY, now=NOW)

    # Mon, Tue, Wed are judged (2 kept); Thursday is still in progress.
    assert (week.habits_kept, week.habits_judged) == (2, 3)
    assert week.habits_kept_share == pytest.approx(2 / 3)
    assert week_so_far(session, as_of=date(2026, 8, 10), now=NOW).habits_kept_share is None


def test_sleep_and_screen_come_from_their_own_views(session):
    for day, hours in ((date(2026, 8, 11), 7), (date(2026, 8, 12), 6)):
        wake = datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(hours=7)
        log_sleep_session(session, started_at=wake - timedelta(hours=hours), ended_at=wake)
    create_screen_category(session, "learning", judgment=ScreenJudgment.USEFUL)
    create_screen_category(session, "social", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "docs", category_slug="learning")
    create_screen_app(session, "feed", category_slug="social")
    log_screen_session(session, "docs", minutes=90, occurred_on=date(2026, 8, 11))
    log_screen_session(session, "feed", minutes=30, occurred_on=date(2026, 8, 12))

    week = week_so_far(session, as_of=TODAY, now=NOW)

    assert week.sleep_nights == 2
    assert week.sleep_average_minutes == pytest.approx(390)
    assert week.screen_score == 75


def test_this_week_compares_the_same_weekdays_of_the_week_before(session):
    week = this_week(session, as_of=TODAY, now=NOW)

    assert (week.week_start, week.week_end, week.complete) == (
        date(2026, 8, 10),
        date(2026, 8, 16),
        False,
    )
    assert (week.current.week_start, week.current.as_of) == (date(2026, 8, 10), TODAY)
    assert (week.previous.week_start, week.previous.as_of) == (date(2026, 8, 3), date(2026, 8, 6))
    assert week.current.sleep_missing_nights == 4
    assert week.habits == []


def test_a_past_sunday_is_a_complete_week(session):
    week = this_week(session, as_of=date(2026, 8, 9), now=NOW)

    assert (week.week_start, week.complete) == (date(2026, 8, 3), True)
    assert week.previous.as_of == date(2026, 8, 2)


def test_tasks_milestones_and_titles_finished_in_the_window(session):
    at = datetime(2026, 8, 11, 10, tzinfo=UTC)
    earlier = datetime(2026, 8, 4, 10, tzinfo=UTC)
    for title, when in (("This week", at), ("Last week", earlier), ("Reopened", at)):
        task = create_task(session, title=title, standalone=True, now=when)
        update_task(session, task.id, {"status": TaskStatus.COMPLETED}, now=when)
        if title == "Reopened":
            update_task(session, task.id, {"status": TaskStatus.TODO}, now=at)
    goal = create_container(session, QuestKind.GOAL, {"title": "Ship"}, now=earlier)
    milestone = create_container(
        session, QuestKind.MILESTONE, {"title": "Beta", "goal_id": goal.id}, now=earlier
    )
    complete_container(session, QuestKind.MILESTONE, milestone.id, override=True, now=at)
    create_library_title(
        session,
        "dune",
        kind=LibraryKind.BOOK,
        status=LibraryStatus.DONE,
        finished_on=date(2026, 8, 12),
    )
    create_library_title(
        session,
        "later",
        kind=LibraryKind.BOOK,
        status=LibraryStatus.DONE,
        finished_on=date(2026, 8, 15),
    )

    week = this_week(session, as_of=TODAY, now=NOW)

    assert week.current.tasks_completed == 1
    assert week.previous.tasks_completed == 1
    assert week.current.milestones_completed == 1
    assert week.previous.milestones_completed == 0
    assert week.current.titles_finished == 1


def test_each_habit_shows_its_progress_for_the_week(session):
    create_habit(
        session,
        name="Read",
        kind=HabitKind.CHECK,
        period=Period.DAY,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    create_habit(
        session,
        name="Run",
        kind=HabitKind.CHECK,
        period=Period.WEEK,
        target_value=3,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    for day in (date(2026, 8, 10), date(2026, 8, 12)):
        log_entry(session, "read", True, occurred_on=day)
    log_entry(session, "run", True, occurred_on=date(2026, 8, 11))

    week = this_week(session, as_of=TODAY, now=NOW)

    rows = {row.slug: row for row in week.habits}
    assert (rows["read"].kept, rows["read"].judged) == (2, 3)
    assert (rows["run"].judged, rows["run"].value, rows["run"].target) == (0, 1, 3)
    assert rows["run"].satisfied is False
    # The pooled number is the sum of the habits' own counts.
    assert (week.current.habits_kept, week.current.habits_judged) == (2, 3)


def test_screen_split_and_sleep_times(session):
    wake = datetime(2026, 8, 12, 7, tzinfo=UTC)
    log_sleep_session(session, started_at=wake - timedelta(hours=8), ended_at=wake)
    create_screen_category(session, "learning", judgment=ScreenJudgment.USEFUL)
    create_screen_category(session, "social", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "docs", category_slug="learning")
    create_screen_app(session, "feed", category_slug="social")
    log_screen_session(session, "docs", minutes=90, occurred_on=date(2026, 8, 11))
    log_screen_session(session, "feed", minutes=30, occurred_on=date(2026, 8, 12))
    log_screen_session(session, "feed", minutes=60, occurred_on=date(2026, 8, 5))

    week = this_week(session, as_of=TODAY, now=NOW)

    assert week.current.sleep_average_bedtime == pytest.approx(-60)
    assert week.current.sleep_average_wake == pytest.approx(420)
    assert (week.current.screen_good, week.current.screen_bad) == (90, 30)
    assert week.current.screen_total == 120
    assert week.current.screen_daily_average == pytest.approx(30)
    assert week.previous.screen_total == 60
