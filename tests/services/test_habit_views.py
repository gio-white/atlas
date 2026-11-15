"""Habit results from the stored facts and the data feeds (habits brief §2–§8)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from atlas.domain import HabitFrequency, HabitMarkResult, ScreenJudgment, TimeOfDay
from atlas.domain.enums import HabitCheck, HabitSource, HabitThreshold, Period
from atlas.domain.habits import DayReason, DayStatus, PeriodState, RuleSpec
from atlas.services import (
    RuleInput,
    add_freeze,
    archive_habit,
    create_habit,
    create_screen_app,
    create_screen_category,
    create_screen_device,
    habit_detail,
    habits_day,
    habits_kept,
    habits_week,
    log_screen_session,
    log_sleep_session,
    set_habit_day,
    this_week,
    week_so_far,
)
from atlas.services.habit_data import HabitData
from atlas.services.habit_views import habit_clock
from atlas.services.quests import create_task
from atlas.services.time_blocks import cancel_time_block, create_time_block

MON = date(2026, 11, 9)
SAT = date(2026, 11, 14)
NOON_SAT = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def utc(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def _manual(session, name: str, *, first_day: date = MON, time_of_day=TimeOfDay.ANYTIME, **rule):
    rule.setdefault("frequency", HabitFrequency.EVERY_DAY)
    return create_habit(
        session, name, RuleInput(**rule), first_day=first_day, time_of_day=time_of_day
    )


def _data(session, name: str, source, threshold, value, *, ref=None, first_day: date = MON):
    rule = RuleInput(
        frequency=HabitFrequency.EVERY_DAY,
        check=HabitCheck.DATA,
        source=source,
        source_ref=ref,
        threshold=threshold,
        value=value,
    )
    return create_habit(session, name, rule, first_day=first_day)


def _screen(session):
    create_screen_category(session, "social", judgment=ScreenJudgment.WASTE)
    create_screen_category(session, "reading", judgment=ScreenJudgment.USEFUL)
    create_screen_app(session, "instagram", category_slug="social")
    create_screen_app(session, "kindle", category_slug="reading")


def _row(day, slug):
    return next(row for row in day.rows if row.view.habit.slug == slug)


# The clock.


def test_today_is_the_current_minute_and_a_past_as_of_is_the_whole_day():
    clock = habit_clock(None, NOON_SAT)
    assert (clock.today, clock.now_minute) == (SAT, 12 * 60)
    past = habit_clock(MON, NOON_SAT)
    assert (past.today, past.now_minute) == (MON, 24 * 60)


# Sleep.


def test_wake_time_reads_the_night_that_ends_on_the_day_and_the_longest_one(session):
    log_sleep_session(session, started_at=_at(MON, 0, 30), ended_at=_at(MON, 6, 48))
    log_sleep_session(session, started_at=_at(MON, 13), ended_at=_at(MON, 13, 40))
    habit = _data(session, "Wake early", HabitSource.WAKE_TIME, HabitThreshold.BEFORE, 7 * 60)
    detail = habit_detail(session, habit.slug, as_of=MON + timedelta(days=2), now=NOON_SAT)
    monday = detail.recent[-1]
    assert (monday.day, monday.status, monday.value) == (MON, DayStatus.DONE, 6 * 60 + 48)
    assert detail.recent[1].reason is DayReason.WAITING_FOR_DATA


def test_a_bedtime_after_midnight_misses_a_before_2330_rule(session):
    tuesday = MON + timedelta(days=1)
    log_sleep_session(session, started_at=_at(tuesday, 0, 40), ended_at=_at(tuesday, 7))
    habit = _data(session, "Bed early", HabitSource.BEDTIME, HabitThreshold.BEFORE, 23 * 60 + 30)
    detail = habit_detail(session, habit.slug, as_of=tuesday, now=NOON_SAT)
    assert (detail.recent[0].status, detail.recent[0].value) == (DayStatus.NOT_DONE, 40)


# Screen time.


def test_screen_time_is_complete_only_when_every_active_device_covers_the_day(session):
    _screen(session)
    create_screen_device(session, "iphone", complete_through=_at(MON + timedelta(days=1), 0))
    create_screen_device(session, "mac", complete_through=_at(MON, 15))
    log_screen_session(session, "instagram", started_at=_at(MON, 9), ended_at=_at(MON, 9, 40))
    data = HabitData.load(session, MON, MON + timedelta(days=1))
    spec = RuleSpec(
        starts_on=MON,
        frequency=HabitFrequency.EVERY_DAY,
        check=HabitCheck.DATA,
        source=HabitSource.SCREEN_BAD_APPS,
        threshold=HabitThreshold.AT_MOST,
        value=90,
    )
    monday = data.reading(spec, MON)
    assert (monday.value, monday.complete, monday.received) == (40, False, True)
    tuesday = data.reading(spec, MON + timedelta(days=1))
    assert (tuesday.value, tuesday.complete, tuesday.received) == (None, False, False)


def test_an_incomplete_day_reads_data_incomplete_and_an_empty_one_no_data_received(session):
    _screen(session)
    create_screen_device(session, "iphone", complete_through=_at(MON, 20))
    log_screen_session(session, "instagram", started_at=_at(MON, 9), ended_at=_at(MON, 9, 30))
    habit = _data(session, "Bad short", HabitSource.SCREEN_BAD_APPS, HabitThreshold.AT_MOST, 90)
    detail = habit_detail(session, habit.slug, as_of=SAT, now=NOON_SAT)
    by_day = {result.day: result for result in detail.recent}
    assert (by_day[MON].status, by_day[MON].reason) == (
        DayStatus.NOT_DONE,
        DayReason.DATA_INCOMPLETE,
    )
    tuesday = by_day[MON + timedelta(days=1)]
    assert (tuesday.status, tuesday.reason) == (DayStatus.NOT_DONE, DayReason.NO_DATA)


def test_a_complete_day_under_the_limit_is_done_and_over_it_is_not(session):
    _screen(session)
    create_screen_device(session, "iphone", complete_through=_at(SAT, 0))
    log_screen_session(session, "instagram", started_at=_at(MON, 9), ended_at=_at(MON, 10))
    tuesday = MON + timedelta(days=1)
    log_screen_session(session, "instagram", started_at=_at(tuesday, 9), ended_at=_at(tuesday, 11))
    log_screen_session(session, "kindle", started_at=_at(tuesday, 20), ended_at=_at(tuesday, 23))
    habit = _data(session, "Bad short", HabitSource.SCREEN_BAD_APPS, HabitThreshold.AT_MOST, 90)
    by_day = {r.day: r for r in habit_detail(session, habit.slug, as_of=SAT, now=NOON_SAT).recent}
    assert (by_day[MON].status, by_day[MON].value) == (DayStatus.DONE, 60)
    assert (by_day[tuesday].status, by_day[tuesday].reason, by_day[tuesday].value) == (
        DayStatus.NOT_DONE,
        DayReason.OVER_LIMIT,
        120,
    )
    app = _data(
        session,
        "Kindle",
        HabitSource.SCREEN_APP,
        HabitThreshold.AT_LEAST,
        60,
        ref="kindle",
    )
    by_day = {r.day: r for r in habit_detail(session, app.slug, as_of=SAT, now=NOON_SAT).recent}
    assert by_day[tuesday].status is DayStatus.DONE
    assert (by_day[MON].status, by_day[MON].value) == (DayStatus.NOT_DONE, 0)


def test_an_archived_device_does_not_hold_the_day_back(session):
    _screen(session)
    create_screen_device(session, "iphone", complete_through=_at(SAT, 0))
    old = create_screen_device(session, "old-phone")
    old.archived_at = _at(MON, 0)
    session.add(old)
    session.commit()
    habit = _data(session, "Bad short", HabitSource.SCREEN_BAD_APPS, HabitThreshold.AT_MOST, 90)
    by_day = {r.day: r for r in habit_detail(session, habit.slug, as_of=SAT, now=NOON_SAT).recent}
    assert by_day[MON].status is DayStatus.DONE


def test_going_over_the_limit_today_is_not_done_at_once(session):
    _screen(session)
    create_screen_device(session, "iphone", complete_through=_at(SAT, 11))
    habit = _data(session, "Bad short", HabitSource.SCREEN_BAD_APPS, HabitThreshold.AT_MOST, 90)
    log_screen_session(session, "instagram", started_at=_at(SAT, 8), ended_at=_at(SAT, 8, 40))
    row = _row(habits_day(session, now=NOON_SAT), habit.slug)
    assert (row.result.status, row.result.value) == (DayStatus.IN_PROGRESS, 40)
    log_screen_session(session, "instagram", started_at=_at(SAT, 9), ended_at=_at(SAT, 10))
    row = _row(habits_day(session, now=NOON_SAT), habit.slug)
    assert (row.result.status, row.result.reason) == (DayStatus.NOT_DONE, DayReason.OVER_LIMIT)


# Sessions planned.


def _planned(session):
    return _data(
        session, "Plan the day", HabitSource.SESSIONS_PLANNED, HabitThreshold.BEFORE, 12 * 60
    )


def test_a_session_planned_before_noon_turns_the_day_done(session):
    habit = _planned(session)
    task = create_task(session, title="Write", standalone=True, now=_at(SAT, 7))
    row = _row(habits_day(session, now=_at(SAT, 9)), habit.slug)
    assert row.result.status is DayStatus.OPEN
    create_time_block(
        session, task_id=task.id, start_at=_at(SAT, 15), end_at=_at(SAT, 16), now=_at(SAT, 8, 10)
    )
    row = _row(habits_day(session, now=_at(SAT, 9)), habit.slug)
    assert (row.result.status, row.result.value) == (DayStatus.DONE, 8 * 60 + 10)


def test_no_session_by_the_cut_off_is_not_done_and_a_cancelled_one_does_not_count(session):
    habit = _planned(session)
    task = create_task(session, title="Write", standalone=True, now=_at(SAT, 7))
    block = create_time_block(
        session, task_id=task.id, start_at=_at(SAT, 15), end_at=_at(SAT, 16), now=_at(SAT, 8)
    )
    cancel_time_block(session, block.id, now=_at(SAT, 8, 30))
    row = _row(habits_day(session, now=_at(SAT, 12, 1)), habit.slug)
    assert row.result.status is DayStatus.NOT_DONE
    create_time_block(
        session, task_id=task.id, start_at=_at(SAT, 17), end_at=_at(SAT, 18), now=_at(SAT, 12, 5)
    )
    row = _row(habits_day(session, now=_at(SAT, 12, 10)), habit.slug)
    assert row.result.status is DayStatus.NOT_DONE


def test_a_session_planned_the_evening_before_counts(session):
    habit = _planned(session)
    friday = SAT - timedelta(days=1)
    task = create_task(session, title="Write", standalone=True, now=_at(friday, 7))
    create_time_block(
        session, task_id=task.id, start_at=_at(SAT, 9), end_at=_at(SAT, 10), now=_at(friday, 21)
    )
    row = _row(habits_day(session, now=_at(SAT, 6)), habit.slug)
    assert (row.result.status, row.result.value) == (DayStatus.DONE, -3 * 60)


# The Day tab.


def test_the_day_lists_scheduled_habits_morning_first_with_the_count_and_strip(session):
    _manual(session, "Read", time_of_day=TimeOfDay.EVENING)
    _manual(session, "Stretch", time_of_day=TimeOfDay.MORNING)
    _manual(session, "Work out", frequency=HabitFrequency.SPECIFIC_DAYS, weekdays=(1, 3, 5))
    _manual(session, "Run", frequency=HabitFrequency.TIMES_A_WEEK, times=2)
    old = _manual(session, "Old")
    archive_habit(session, old.slug)
    set_habit_day(session, "stretch", SAT, HabitMarkResult.DONE, today=SAT)
    set_habit_day(session, "run", MON, HabitMarkResult.DONE, today=SAT)
    day = habits_day(session, now=NOON_SAT)
    assert [row.view.habit.name for row in day.rows] == ["Stretch", "Read", "Run"]
    assert (day.done, day.total) == (1, 3)
    run = _row(day, "run")
    assert (run.progress.period, run.progress.done, run.progress.target) == (Period.WEEK, 1, 2)
    assert [(count.done, count.total) for count in day.week[:2]] == [(1, 4), (0, 3)]
    assert (day.week[-1].done, day.week[-1].total) == (0, 0)


def test_a_past_as_of_day_is_today_at_its_end(session):
    _manual(session, "Read")
    day = habits_day(session, as_of=MON + timedelta(days=1), now=NOON_SAT)
    assert day.day == MON + timedelta(days=1)
    assert day.rows[0].result.status is DayStatus.OPEN
    assert day.week[0].total == 1


def test_the_streak_counts_the_habit_s_own_period(session):
    habit = _manual(session, "Read", first_day=MON - timedelta(days=7))
    for offset in range(-7, 5):
        set_habit_day(session, habit.slug, MON + timedelta(days=offset), HabitMarkResult.DONE)
    row = _row(habits_day(session, now=NOON_SAT), habit.slug)
    assert (row.streak.count, row.streak.period) == (12, Period.DAY)


def test_freezing_a_holiday_keeps_the_streak(session):
    habit = _manual(session, "Read", first_day=MON - timedelta(days=7))
    for offset in range(-7, 0):
        set_habit_day(session, habit.slug, MON + timedelta(days=offset), HabitMarkResult.DONE)
    add_freeze(session, start_on=MON, end_on=SAT - timedelta(days=1), reason="Holiday")
    row = _row(habits_day(session, now=NOON_SAT), habit.slug)
    assert row.streak.count == 7


# The Week tab, Habits kept, and one habit.


def test_the_week_shows_each_day_and_habits_kept_against_last_week(session):
    habit = _manual(session, "Read", first_day=MON - timedelta(days=7))
    for offset in (-7, -6, -5, 0, 1, 2, 3):
        set_habit_day(session, habit.slug, MON + timedelta(days=offset), HabitMarkResult.DONE)
    week = habits_week(session, now=NOON_SAT)
    statuses = [day.status for day in week.rows[0].days]
    assert statuses[:5] == [DayStatus.DONE] * 4 + [DayStatus.NOT_DONE]
    assert statuses[5:] == [DayStatus.OPEN, DayStatus.UPCOMING]
    assert (week.kept.done, week.kept.target) == (4, 5)
    assert (week.kept_last_week.done, week.kept_last_week.target) == (3, 5)


def test_habits_kept_agrees_on_home_this_week_and_the_week_tab(session):
    habit = _manual(session, "Read")
    _manual(session, "Run", frequency=HabitFrequency.TIMES_A_WEEK, times=3)
    for offset in (0, 2):
        set_habit_day(session, habit.slug, MON + timedelta(days=offset), HabitMarkResult.DONE)
    set_habit_day(session, "run", MON, HabitMarkResult.DONE)
    week = habits_week(session, as_of=SAT, now=NOON_SAT)
    home = week_so_far(session, as_of=SAT, now=NOON_SAT)
    stats = this_week(session, as_of=SAT, now=NOON_SAT)
    assert (week.kept.done, week.kept.target) == (3, 8)
    assert (home.habits_kept, home.habits_judged) == (3, 8)
    assert stats.current.habits_kept_share == week.kept.share
    assert sum(row.done for row in stats.habits) == 3
    assert sum(row.target for row in stats.habits) == 8
    assert habits_kept(session, MON, SAT, now=NOON_SAT).share == 3 / 8


def test_the_habit_page_has_streaks_kept_history_recent_days_and_freezes(session):
    first = SAT - timedelta(days=40)
    habit = _manual(session, "Read", first_day=first)
    for offset in range(0, 41, 2):
        set_habit_day(session, habit.slug, first + timedelta(days=offset), HabitMarkResult.DONE)
    add_freeze(session, start_on=SAT, end_on=SAT, reason="Ill", habit_slug=habit.slug)
    detail = habit_detail(session, habit.slug, now=NOON_SAT)
    assert detail.current_streak.count == 0  # Friday was not ticked; Saturday is frozen
    assert detail.best_streak == 1
    assert (detail.kept_last_4_weeks.done, detail.kept_last_4_weeks.target) == (14, 28)
    assert detail.history[0].start == first
    assert len(detail.recent) == 14
    assert detail.recent[0].status is DayStatus.FROZEN
    assert [freeze.reason for freeze in detail.freezes] == ["Ill"]
    assert detail.history[-1].state is PeriodState.FROZEN
