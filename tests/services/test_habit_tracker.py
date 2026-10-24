from datetime import date

import pytest
from sqlmodel import select

from atlas.db import Area, Metric
from atlas.domain import Comparator, Direction, HabitKind, Period, TimeOfDay, ValueType
from atlas.services import (
    HABITS_AREA_SLUG,
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    add_habit_break,
    archive_habit,
    check_in,
    create_habit,
    delete_habit,
    delete_habit_break,
    export_all,
    get_habit,
    habit_detail,
    habit_status,
    habits_board,
    import_all,
    list_habit_breaks,
    unarchive_habit,
    undo_check_in,
    update_habit,
)

START = date(2026, 8, 3)


def _metric(session, slug: str) -> Metric:
    return session.exec(select(Metric).where(Metric.slug == slug)).one()


def test_habit_first_create_makes_the_metric_in_the_habits_area(session):
    habit = create_habit(
        session,
        name="Read 20 pages",
        kind=HabitKind.COUNT,
        period=Period.DAY,
        target_value=20,
        unit="pages",
        time_of_day=TimeOfDay.EVENING,
        active_from=START,
    )
    assert habit.slug == "read-20-pages"
    assert habit.kind is HabitKind.COUNT
    assert habit.time_of_day is TimeOfDay.EVENING
    metric = _metric(session, "read-20-pages")
    assert ValueType(metric.value_type) is ValueType.COUNT
    assert metric.unit == "pages"
    assert Direction(metric.direction) is Direction.HIGHER_IS_BETTER
    area = session.get(Area, metric.area_id)
    assert area.slug == HABITS_AREA_SLUG

    with pytest.raises(AlreadyExistsError):
        create_habit(session, name="Read 20 pages", period=Period.DAY, target_value=1)


def test_each_kind_gets_a_matching_metric(session):
    check = create_habit(session, name="Stretch", kind=HabitKind.CHECK, period=Period.DAY)
    timer = create_habit(
        session, name="Practice", kind=HabitKind.DURATION, period=Period.WEEK, target_value=120
    )
    quit_habit = create_habit(
        session,
        name="No sugar",
        kind=HabitKind.QUIT,
        period=Period.WEEK,
        target_value=5,
        comparator=Comparator.AT_LEAST,
    )
    assert check.target_value == 1.0
    assert ValueType(_metric(session, "stretch").value_type) is ValueType.BOOL
    assert _metric(session, "practice").unit == "min"
    assert timer.period is Period.WEEK
    assert (quit_habit.period, quit_habit.comparator, quit_habit.target_value) == (
        Period.DAY,
        Comparator.AT_MOST,
        0.0,
    )
    assert Direction(_metric(session, "no-sugar").direction) is Direction.LOWER_IS_BETTER
    with pytest.raises(ValidationError):
        create_habit(session, name="Pushups", kind=HabitKind.COUNT, period=Period.DAY)


def test_metric_slug_collisions_get_a_suffix(session):
    create_habit(session, name="Walk", kind=HabitKind.CHECK, period=Period.DAY)
    delete_habit(session, "walk")
    again = create_habit(session, name="Walk", kind=HabitKind.CHECK, period=Period.DAY)
    assert again.slug == "walk"
    assert _metric(session, "walk-2").archived_at is None
    assert _metric(session, "walk").archived_at is not None


def test_check_ins_per_kind_and_undo(session):
    create_habit(
        session, name="Stretch", kind=HabitKind.CHECK, period=Period.DAY, active_from=START
    )
    create_habit(
        session,
        name="Pushups",
        kind=HabitKind.COUNT,
        period=Period.DAY,
        target_value=40,
        active_from=START,
    )
    create_habit(
        session, name="No sugar", kind=HabitKind.QUIT, period=Period.DAY, active_from=START
    )
    day = date(2026, 8, 10)

    status = check_in(session, "stretch", on=day, as_of=day)
    assert status.satisfied and status.today_value == 1.0
    assert check_in(session, "stretch", on=day, as_of=day).today_value == 1.0
    assert undo_check_in(session, "stretch", on=day, as_of=day).today_value is None

    check_in(session, "pushups", amount=25, on=day, as_of=day)
    status = check_in(session, "pushups", amount=15, on=day, as_of=day)
    assert status.current_value == 40.0 and status.satisfied
    assert undo_check_in(session, "pushups", on=day, as_of=day).current_value == 25.0
    assert check_in(session, "pushups", on=day, as_of=day).current_value == 26.0

    assert habit_status(session, "no-sugar", as_of=day).current_streak == 8
    status = check_in(session, "no-sugar", on=day, note="birthday cake", as_of=day)
    assert status.current_streak == 0
    assert status.last_entry_on == day
    assert habit_detail(session, "no-sugar", as_of=day).recent[0].note == "birthday cake"

    with pytest.raises(ValidationError):
        check_in(session, "stretch", on=date(2026, 8, 11), as_of=day)
    with pytest.raises(ValidationError):
        check_in(session, "pushups", amount=0, as_of=day)
    with pytest.raises(ValidationError):
        undo_check_in(session, "stretch", on=date(2026, 8, 4), as_of=day)


def test_breaks_excuse_days_and_scale_weekly_targets(session):
    create_habit(
        session, name="Stretch", kind=HabitKind.CHECK, period=Period.DAY, active_from=START
    )
    create_habit(
        session,
        name="Runs",
        kind=HabitKind.COUNT,
        period=Period.WEEK,
        target_value=3,
        active_from=START,
    )
    for day in (3, 4, 5, 8, 9):
        check_in(session, "stretch", on=date(2026, 8, day), as_of=date(2026, 8, 9))
    pause = add_habit_break(session, "stretch", date(2026, 8, 6), date(2026, 8, 7), note="Travel")
    skip = add_habit_break(session, "stretch", date(2026, 8, 10))
    assert skip.end_on == date(2026, 8, 10)

    status = habit_status(session, "stretch", as_of=date(2026, 8, 10))
    assert status.current_streak == 5
    assert status.excused and status.skipped_today
    assert status.effective_target is None

    add_habit_break(session, "runs", date(2026, 8, 10), date(2026, 8, 12))
    runs = habit_status(session, "runs", as_of=date(2026, 8, 13))
    assert runs.effective_target == 2.0

    assert [row.id for row in list_habit_breaks(session, "stretch")] == [pause.id, skip.id]
    delete_habit_break(session, "stretch", skip.id)
    assert not habit_status(session, "stretch", as_of=date(2026, 8, 10)).excused
    with pytest.raises(NotFoundError):
        delete_habit_break(session, "runs", pause.id)
    with pytest.raises(ValidationError):
        add_habit_break(session, "stretch", date(2026, 8, 12), date(2026, 8, 11))


def test_edit_archive_and_board(session):
    create_habit(
        session, name="Stretch", kind=HabitKind.CHECK, period=Period.DAY, active_from=START
    )
    create_habit(session, name="Floss", kind=HabitKind.CHECK, period=Period.DAY, active_from=START)
    as_of = date(2026, 8, 10)
    for day in range(3, 11):
        check_in(session, "stretch", on=date(2026, 8, day), as_of=as_of)

    updated = update_habit(
        session, "stretch", name="Morning stretch", time_of_day=TimeOfDay.MORNING, unit="sets"
    )
    assert updated.name == "Morning stretch"
    assert habit_status(session, "stretch", as_of=as_of).unit == "sets"

    board = habits_board(session, as_of=as_of)
    assert (board.scheduled, board.satisfied) == (2, 1)
    assert board.completion_7d == 7 / 14

    archive_habit(session, "floss")
    board = habits_board(session, as_of=as_of)
    assert [status.slug for status in board.day] == ["stretch"]
    assert board.completion_7d == 1.0
    with pytest.raises(ValidationError):
        archive_habit(session, "floss")
    unarchive_habit(session, "floss")
    assert len(habits_board(session, as_of=as_of).day) == 2

    quit_habit = create_habit(session, name="No sugar", kind=HabitKind.QUIT, period=Period.DAY)
    with pytest.raises(ValidationError):
        update_habit(session, quit_habit.slug, target_value=2)


def test_export_import_round_trips_habit_fields(session):
    create_habit(
        session,
        name="Stretch",
        kind=HabitKind.CHECK,
        period=Period.DAY,
        time_of_day=TimeOfDay.MORNING,
        active_from=START,
    )
    add_habit_break(session, "stretch", date(2026, 8, 6), note="Travel")
    archive_habit(session, "stretch")
    payload = export_all(session)
    row = payload["habits"][0]
    assert row["kind"] == "check"
    assert row["time_of_day"] == "morning"
    assert row["breaks"] == [{"start_on": "2026-08-06", "end_on": "2026-08-06", "note": "Travel"}]
    assert row["archived_at"] is not None

    import_all(session, payload, replace=True)
    restored = get_habit(session, "stretch")
    assert restored.kind is HabitKind.CHECK
    assert restored.archived_at is not None
    assert list_habit_breaks(session, "stretch")[0].note == "Travel"

    legacy = {**payload, "schema_version": 9}
    legacy["habits"] = [{key: value for key, value in row.items() if key not in {"kind", "breaks"}}]
    import_all(session, legacy, replace=True)
    assert get_habit(session, "stretch").kind is HabitKind.CHECK
    assert list_habit_breaks(session, "stretch") == []
