from datetime import UTC, date, datetime

import pytest
from sqlmodel import select

from atlas.db.models import HabitFreeze, HabitMark, HabitRule, ScreenApp
from atlas.domain import (
    HabitApply,
    HabitCheck,
    HabitFrequency,
    HabitMarkResult,
    HabitSource,
    HabitThreshold,
    ScreenJudgment,
    TimeOfDay,
)
from atlas.services import (
    ARCHIVED_REASON,
    AlreadyExistsError,
    NotFoundError,
    RuleInput,
    ValidationError,
    add_freeze,
    archive_habit,
    clear_habit_day,
    create_habit,
    create_screen_app,
    create_screen_category,
    delete_freeze,
    delete_habit,
    get_habit,
    habit_marks,
    habit_rules,
    habit_view,
    list_freezes,
    list_habits,
    restore_habit,
    rule_on,
    set_habit_day,
    update_habit,
)
from tests.services.helpers import seed_daily_pushups

EVERY_DAY = RuleInput(frequency=HabitFrequency.EVERY_DAY)


def _wake_rule(**fields) -> RuleInput:
    return RuleInput(
        frequency=HabitFrequency.EVERY_DAY,
        check=HabitCheck.DATA,
        source=HabitSource.WAKE_TIME,
        **fields,
    )


def test_create_habit_stores_the_first_rule_version_from_the_first_day(session):
    habit = create_habit(
        session,
        "  Morning pushups ",
        RuleInput(frequency=HabitFrequency.SPECIFIC_DAYS, weekdays=(5, 1, 3, 1)),
        time_of_day=TimeOfDay.MORNING,
        first_day=date(2026, 8, 1),
    )

    assert habit.slug == "morning-pushups"
    assert habit.name == "Morning pushups"
    assert habit.first_day == date(2026, 8, 1)
    [rule] = habit_rules(session, habit)
    assert rule.starts_on == date(2026, 8, 1)
    assert rule.frequency == HabitFrequency.SPECIFIC_DAYS
    assert rule.weekdays == [1, 3, 5]
    assert rule.check == HabitCheck.MANUAL
    assert rule.source is None


def test_create_habit_rejects_a_duplicate_slug_and_an_empty_name(session):
    seed_daily_pushups(session)
    with pytest.raises(AlreadyExistsError):
        create_habit(session, "Pushups again", EVERY_DAY, slug="pushups-daily")
    with pytest.raises(ValidationError, match="needs a name"):
        create_habit(session, "  ", EVERY_DAY)


@pytest.mark.parametrize(
    ("rule", "message"),
    [
        (RuleInput(frequency=HabitFrequency.SPECIFIC_DAYS), "pick at least one day"),
        (
            RuleInput(frequency=HabitFrequency.SPECIFIC_DAYS, weekdays=(0, 2)),
            "1 \\(Monday\\) to 7",
        ),
        (RuleInput(frequency=HabitFrequency.EVERY_DAY, weekdays=(1,)), "only set for specific"),
        (RuleInput(frequency=HabitFrequency.TIMES_A_WEEK), "times must be 1 to 7"),
        (RuleInput(frequency=HabitFrequency.TIMES_A_WEEK, times=8), "times must be 1 to 7"),
        (RuleInput(frequency=HabitFrequency.TIMES_A_MONTH, times=32), "times must be 1 to 31"),
        (RuleInput(frequency=HabitFrequency.EVERY_DAY, times=2), "only set for times"),
        (RuleInput(frequency=HabitFrequency.EVERY_DAY, value=5), "no source or threshold"),
        (
            RuleInput(frequency=HabitFrequency.EVERY_DAY, check=HabitCheck.DATA),
            "needs a source",
        ),
        (_wake_rule(threshold=HabitThreshold.AT_LEAST), "Wake time takes before, after"),
        (_wake_rule(value=24 * 60), "between 00:00 and 23:59"),
        (
            RuleInput(
                frequency=HabitFrequency.EVERY_DAY,
                check=HabitCheck.DATA,
                source=HabitSource.SCREEN_TOTAL,
                value=0,
            ),
            "more than 0",
        ),
        (_wake_rule(source_ref="youtube"), "does not take a category or app"),
        (
            RuleInput(
                frequency=HabitFrequency.EVERY_DAY,
                check=HabitCheck.DATA,
                source=HabitSource.SCREEN_APP,
            ),
            "pick a app",
        ),
    ],
)
def test_validate_rule_rejects_a_rule_that_does_not_fit(session, rule, message):
    with pytest.raises(ValidationError, match=message):
        create_habit(session, "Habit", rule)


def test_a_data_habit_takes_the_source_defaults(session):
    habit = create_habit(session, "Wake up early", _wake_rule(), first_day=date(2026, 8, 1))

    rule = habit_view(session, habit, on=date(2026, 8, 2)).rule
    assert rule.check == HabitCheck.DATA
    assert rule.threshold == HabitThreshold.BEFORE
    assert rule.value == 7 * 60


def test_a_screen_app_habit_names_an_active_app(session):
    create_screen_category(session, "social", judgment=ScreenJudgment.WASTE)
    app = create_screen_app(session, "instagram", category_slug="social", name="Instagram")
    rule = RuleInput(
        frequency=HabitFrequency.EVERY_DAY,
        check=HabitCheck.DATA,
        source=HabitSource.SCREEN_APP,
        source_ref="instagram",
        threshold=HabitThreshold.AT_MOST,
        value=30,
    )

    habit = create_habit(session, "Instagram short", rule)
    assert habit_view(session, habit).source_ref_name == "Instagram"

    stored = session.get(ScreenApp, app.id)
    stored.archived_at = datetime.now(UTC)
    session.add(stored)
    session.commit()
    with pytest.raises(ValidationError, match="archived"):
        create_habit(session, "Instagram again", rule)


def test_list_habits_orders_by_name_and_can_hide_archived(session):
    create_habit(session, "Read", EVERY_DAY)
    create_habit(session, "Meditate", EVERY_DAY)
    archive_habit(session, "read")

    assert [habit.slug for habit in list_habits(session)] == ["meditate", "read"]
    assert [habit.slug for habit in list_habits(session, include_archived=False)] == ["meditate"]


def test_a_rule_change_from_today_adds_a_version_and_keeps_the_past(session):
    seed_daily_pushups(session)
    weekdays = RuleInput(frequency=HabitFrequency.SPECIFIC_DAYS, weekdays=(1, 2, 3, 4, 5))

    habit = update_habit(session, "pushups-daily", rule=weekdays, today=date(2026, 8, 10))

    rules = habit_rules(session, habit)
    assert [rule.starts_on for rule in rules] == [date(2026, 8, 1), date(2026, 8, 10)]
    assert rule_on(rules, date(2026, 8, 9)).frequency == HabitFrequency.EVERY_DAY
    assert rule_on(rules, date(2026, 8, 10)).frequency == HabitFrequency.SPECIFIC_DAYS


def test_a_second_change_on_the_same_day_replaces_that_day_s_version(session):
    seed_daily_pushups(session)
    today = date(2026, 8, 10)
    update_habit(
        session,
        "pushups-daily",
        rule=RuleInput(frequency=HabitFrequency.TIMES_A_WEEK, times=3),
        today=today,
    )
    habit = update_habit(
        session,
        "pushups-daily",
        rule=RuleInput(frequency=HabitFrequency.TIMES_A_WEEK, times=4),
        today=today,
    )

    rules = habit_rules(session, habit)
    assert [(rule.starts_on, rule.times) for rule in rules] == [
        (date(2026, 8, 1), None),
        (today, 4),
    ]


def test_an_unchanged_rule_stores_nothing(session):
    seed_daily_pushups(session)
    habit = update_habit(session, "pushups-daily", rule=EVERY_DAY, today=date(2026, 8, 10))
    assert len(habit_rules(session, habit)) == 1


def test_a_rule_change_for_all_days_replaces_every_version(session):
    seed_daily_pushups(session)
    update_habit(
        session,
        "pushups-daily",
        rule=RuleInput(frequency=HabitFrequency.TIMES_A_WEEK, times=3),
        today=date(2026, 8, 10),
    )
    habit = update_habit(
        session,
        "pushups-daily",
        rule=RuleInput(frequency=HabitFrequency.TIMES_A_WEEK, times=2),
        apply=HabitApply.ALL_DAYS,
    )

    [rule] = habit_rules(session, habit)
    assert (rule.starts_on, rule.times) == (date(2026, 8, 1), 2)


def test_rename_and_time_of_day_are_not_versioned(session):
    seed_daily_pushups(session)
    habit = update_habit(session, "pushups-daily", name="Pushups", time_of_day=TimeOfDay.EVENING)

    assert habit.name == "Pushups"
    assert habit.time_of_day == TimeOfDay.EVENING
    assert len(habit_rules(session, habit)) == 1
    with pytest.raises(ValidationError):
        update_habit(session, "pushups-daily", name=" ")


def test_a_manual_tick_is_stored_and_not_done_removes_it(session):
    seed_daily_pushups(session)
    day = date(2026, 8, 5)

    mark = set_habit_day(session, "pushups-daily", day, HabitMarkResult.DONE)
    assert mark is not None and mark.result == HabitMarkResult.DONE

    assert set_habit_day(session, "pushups-daily", day, HabitMarkResult.NOT_DONE) is None
    assert habit_marks(session, get_habit(session, "pushups-daily")) == []


def test_a_data_habit_keeps_either_answer(session):
    create_habit(session, "Wake up early", _wake_rule(), slug="wake", first_day=date(2026, 8, 1))
    day = date(2026, 8, 5)

    mark = set_habit_day(session, "wake", day, HabitMarkResult.NOT_DONE)
    assert mark is not None and mark.result == HabitMarkResult.NOT_DONE
    mark = set_habit_day(session, "wake", day, HabitMarkResult.DONE)
    assert mark.result == HabitMarkResult.DONE
    assert len(habit_marks(session, get_habit(session, "wake"))) == 1

    clear_habit_day(session, "wake", day)
    clear_habit_day(session, "wake", day)
    assert habit_marks(session, get_habit(session, "wake")) == []


def test_a_day_before_the_first_day_or_in_the_future_cannot_be_answered(session):
    seed_daily_pushups(session)
    with pytest.raises(ValidationError, match="starts on 2026-08-01"):
        set_habit_day(session, "pushups-daily", date(2026, 7, 31), HabitMarkResult.DONE)
    with pytest.raises(ValidationError, match="future"):
        set_habit_day(
            session,
            "pushups-daily",
            date(2026, 8, 11),
            HabitMarkResult.DONE,
            today=date(2026, 8, 10),
        )


def test_archive_then_restore_freezes_the_archived_days(session):
    habit = seed_daily_pushups(session)
    archive_habit(session, "pushups-daily")
    habit.archived_at = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    session.add(habit)
    session.commit()
    with pytest.raises(ValidationError, match="already archived"):
        archive_habit(session, "pushups-daily")

    restored = restore_habit(session, "pushups-daily", today=date(2026, 8, 9))

    assert restored.archived_at is None
    [freeze] = list_freezes(session, habit_slug="pushups-daily")
    assert (freeze.start_on, freeze.end_on, freeze.reason) == (
        date(2026, 8, 5),
        date(2026, 8, 8),
        ARCHIVED_REASON,
    )
    with pytest.raises(ValidationError, match="not archived"):
        restore_habit(session, "pushups-daily")


def test_restoring_on_the_day_it_was_archived_adds_no_freeze(session):
    seed_daily_pushups(session)
    archived = archive_habit(session, "pushups-daily")
    restore_habit(session, "pushups-daily", today=archived.archived_at.date())
    assert list_freezes(session) == []


def test_delete_habit_removes_its_history_but_not_all_habit_freezes(session):
    habit = seed_daily_pushups(session)
    set_habit_day(session, "pushups-daily", date(2026, 8, 5), HabitMarkResult.DONE)
    add_freeze(session, start_on=date(2026, 8, 6), habit_slug="pushups-daily")
    everyone = add_freeze(session, start_on=date(2026, 8, 7), reason="Holiday")

    delete_habit(session, "pushups-daily")

    with pytest.raises(NotFoundError):
        get_habit(session, "pushups-daily")
    for model in (HabitRule, HabitMark):
        assert session.exec(select(model).where(model.habit_id == habit.id)).all() == []
    assert [row.id for row in session.exec(select(HabitFreeze)).all()] == [everyone.id]


def test_freezes_cover_one_habit_or_all_and_list_newest_first(session):
    seed_daily_pushups(session)
    create_habit(session, "Read", EVERY_DAY)
    holiday = add_freeze(
        session, start_on=date(2026, 8, 10), end_on=date(2026, 8, 12), reason=" Holiday "
    )
    sick = add_freeze(session, start_on=date(2026, 8, 4), habit_slug="pushups-daily")
    reading = add_freeze(session, start_on=date(2026, 8, 6), habit_slug="read")

    assert holiday.habit_id is None and holiday.reason == "Holiday"
    assert (sick.start_on, sick.end_on, sick.reason) == (date(2026, 8, 4), date(2026, 8, 4), None)
    assert [row.id for row in list_freezes(session)] == [holiday.id, reading.id, sick.id]
    assert [row.id for row in list_freezes(session, habit_slug="pushups-daily")] == [
        holiday.id,
        sick.id,
    ]

    delete_freeze(session, sick.id)
    with pytest.raises(NotFoundError):
        delete_freeze(session, sick.id)
    with pytest.raises(ValidationError, match="on or after"):
        add_freeze(session, start_on=date(2026, 8, 5), end_on=date(2026, 8, 4))
