from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from atlas.db import (
    CURRENT_SCHEMA_VERSION,
    Ambition,
    Chapter,
    Goal,
    Habit,
    HabitRule,
    HabitSupport,
    Milestone,
    SchemaVersion,
    SideQuest,
    Task,
    TimeBlock,
    create_engine_for,
    create_memory_engine,
    init_schema,
    make_session_factory,
)
from atlas.domain import HabitCheck, HabitFrequency, TaskStatus
from atlas.services import RuleInput, create_habit

NOW = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)
QUEST_TABLES = {"ambition", "goal", "milestone", "side_quest", "chapter", "task", "time_block"}


@pytest.fixture
def engine():
    memory = create_memory_engine()
    init_schema(memory)
    return memory


@pytest.fixture
def session(engine):
    with make_session_factory(engine)() as db_session:
        yield db_session


def _add(session: Session, row):
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_schema_has_the_seven_quest_tables(engine):
    assert set(inspect(engine).get_table_names()) >= QUEST_TABLES
    assert CURRENT_SCHEMA_VERSION >= 11


def test_every_quest_foreign_key_is_restrict_and_indexed(engine):
    inspector = inspect(engine)
    for table in QUEST_TABLES:
        indexed = {
            column for index in inspector.get_indexes(table) for column in index["column_names"]
        }
        for key in inspector.get_foreign_keys(table):
            assert key["options"].get("ondelete") == "RESTRICT", (table, key)
            assert set(key["constrained_columns"]) <= indexed, (table, key)
    task_indexed = {c for i in inspector.get_indexes("task") for c in i["column_names"]}
    block_indexed = {c for i in inspector.get_indexes("time_block") for c in i["column_names"]}
    assert "organized_at" in task_indexed
    assert "start_at" in block_indexed


def test_chapter_needs_exactly_one_parent(session):
    goal = _add(session, Goal(title="Move to Copenhagen"))
    milestone = _add(session, Milestone(goal_id=goal.id, title="Find a job"))
    side = _add(session, SideQuest(title="Taxes"))
    session.add(Chapter(title="Orphan"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(Chapter(title="Both", milestone_id=milestone.id, side_quest_id=side.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_task_has_at_most_one_parent(session):
    ambition = _add(session, Ambition(title="Grow"))
    goal = _add(session, Goal(title="Ship"))
    session.add(Task(title="Both", ambition_id=ambition.id, goal_id=goal.id, organized_at=NOW))
    with pytest.raises(IntegrityError):
        session.commit()


def test_task_with_a_parent_must_be_organized(session):
    goal = _add(session, Goal(title="Ship"))
    session.add(Task(title="Unorganized", goal_id=goal.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_task_completed_status_matches_completed_at(session):
    session.add(Task(title="Done but no time", status=TaskStatus.COMPLETED))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(Task(title="Time but open", completed_at=NOW))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    done = _add(session, Task(title="Done", status=TaskStatus.COMPLETED, completed_at=NOW))
    assert done.id is not None


def test_task_estimate_must_be_positive(session):
    session.add(Task(title="Zero", estimate_minutes=0))
    with pytest.raises(IntegrityError):
        session.commit()


def test_time_block_must_end_after_it_starts(session):
    task = _add(session, Task(title="Read"))
    session.add(TimeBlock(task_id=task.id, start_at=NOW, end_at=NOW))
    with pytest.raises(IntegrityError):
        session.commit()


def test_time_block_external_event_is_unique_per_provider(session):
    task = _add(session, Task(title="Read"))
    end = NOW + timedelta(hours=1)
    _add(session, TimeBlock(task_id=task.id, start_at=NOW, end_at=end))
    _add(session, TimeBlock(task_id=task.id, start_at=NOW, end_at=end))
    _add(session, TimeBlock(task_id=task.id, start_at=NOW, end_at=end, external_event_id="e1"))
    session.add(TimeBlock(task_id=task.id, start_at=NOW, end_at=end, external_event_id="e1"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_a_parent_with_children_is_restricted(session):
    goal = _add(session, Goal(title="Ship"))
    _add(session, Milestone(goal_id=goal.id, title="Beta"))
    session.delete(goal)
    with pytest.raises(IntegrityError):
        session.commit()


def _v10_database(path):
    engine = create_engine_for(path)
    statements = [
        "CREATE TABLE area (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL, name VARCHAR NOT NULL,"
        " description VARCHAR, archived_at DATETIME)",
        "CREATE UNIQUE INDEX ix_area_slug ON area (slug)",
        "CREATE TABLE metric (id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL REFERENCES area(id),"
        " slug VARCHAR NOT NULL, name VARCHAR NOT NULL, value_type VARCHAR NOT NULL,"
        " unit VARCHAR, aggregation VARCHAR NOT NULL, direction VARCHAR NOT NULL,"
        " archived_at DATETIME)",
        "CREATE TABLE goal (id INTEGER PRIMARY KEY, area_id INTEGER REFERENCES area(id),"
        " slug VARCHAR NOT NULL, name VARCHAR NOT NULL, kind VARCHAR NOT NULL,"
        " metric_id INTEGER REFERENCES metric(id), target_value FLOAT, comparator VARCHAR,"
        " baseline_value FLOAT, measure VARCHAR, start_on DATE NOT NULL, due_on DATE NOT NULL,"
        " horizon VARCHAR NOT NULL, parent_id INTEGER REFERENCES goal(id), description TEXT,"
        " status VARCHAR NOT NULL, achieved_at DATETIME)",
        "CREATE UNIQUE INDEX ix_goal_slug ON goal (slug)",
        "CREATE TABLE milestone (id INTEGER PRIMARY KEY,"
        " goal_id INTEGER NOT NULL REFERENCES goal(id), name VARCHAR NOT NULL, due_on DATE,"
        " done_at DATETIME)",
        "CREATE TABLE task (id INTEGER PRIMARY KEY, title VARCHAR NOT NULL,"
        " bucket VARCHAR NOT NULL, due_on DATE, due_at DATETIME, priority VARCHAR NOT NULL,"
        " goal_id INTEGER REFERENCES goal(id), done_at DATETIME, created_at DATETIME NOT NULL)",
        "CREATE TABLE habit (id INTEGER PRIMARY KEY,"
        " metric_id INTEGER NOT NULL REFERENCES metric(id), slug VARCHAR NOT NULL,"
        " name VARCHAR NOT NULL, period VARCHAR NOT NULL, target_value FLOAT NOT NULL,"
        " comparator VARCHAR NOT NULL, weekdays JSON, active_from DATE NOT NULL, active_to DATE,"
        " kind VARCHAR NOT NULL, time_of_day VARCHAR NOT NULL,"
        " goal_id INTEGER REFERENCES goal(id), archived_at DATETIME)",
        "CREATE UNIQUE INDEX ix_habit_slug ON habit (slug)",
        "CREATE TABLE habit_break (id INTEGER PRIMARY KEY,"
        " habit_id INTEGER NOT NULL REFERENCES habit(id), start_on DATE NOT NULL,"
        " end_on DATE NOT NULL, note VARCHAR, created_at DATETIME NOT NULL)",
        "CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER NOT NULL)",
        "INSERT INTO schema_version VALUES (1, 10)",
        "INSERT INTO area VALUES (1, 'health', 'Health', NULL, NULL)",
        "INSERT INTO metric VALUES (1, 1, 'pushups', 'Pushups', 'COUNT', 'reps', 'SUM',"
        " 'HIGHER_IS_BETTER', NULL)",
        "INSERT INTO goal VALUES (1, 1, 'strong', 'Strong', 'MILESTONE', NULL, NULL, NULL, NULL,"
        " NULL, '2026-01-01', '2026-12-31', 'LONG', NULL, NULL, 'ACTIVE', NULL)",
        "INSERT INTO milestone VALUES (1, 1, '50 pushups', NULL, NULL)",
        "INSERT INTO task VALUES (1, 'Do pushups', 'TODAY', NULL, NULL, 'NORMAL', 1, NULL,"
        " '2026-11-01 12:00:00')",
        "INSERT INTO habit VALUES (1, 1, 'pushups-daily', 'Pushups', 'DAY', 20, 'AT_LEAST',"
        " NULL, '2026-08-01', NULL, 'COUNT', 'MORNING', 1, NULL)",
        "INSERT INTO habit_break VALUES (1, 1, '2026-08-10', '2026-08-12', 'Travel',"
        " '2026-08-09 12:00:00')",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return engine


def test_init_schema_migrates_a_v10_database_to_quests(tmp_path):
    engine = _v10_database(tmp_path / "v10.db")

    init_schema(engine)

    inspector = inspect(engine)
    assert set(inspector.get_table_names()) >= QUEST_TABLES
    goal_columns = {column["name"] for column in inspector.get_columns("goal")}
    assert "slug" not in goal_columns
    assert {"ambition_id", "success_description", "title"} <= goal_columns
    assert "bucket" not in {column["name"] for column in inspector.get_columns("task")}
    assert "goal_id" not in {column["name"] for column in inspector.get_columns("habit")}
    assert any(index["unique"] for index in inspector.get_indexes("habit"))
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION
        assert session.exec(select(Goal)).all() == []
        assert session.exec(select(Task)).all() == []
        habit = session.exec(select(Habit)).one()
        assert (habit.slug, habit.first_day, habit.time_of_day.value) == (
            "pushups-daily",
            date(2026, 8, 1),
            "morning",
        )
        rule = session.exec(select(HabitRule)).one()
        assert (rule.frequency, rule.check) == (HabitFrequency.EVERY_DAY, HabitCheck.MANUAL)
        habit.name = "Pushups every day"
        session.add(habit)
        session.commit()
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
        freezes = connection.execute(text("SELECT habit_id, reason FROM habit_freeze")).all()
        assert "habit_break" not in inspect(engine).get_table_names()
    assert [tuple(row) for row in freezes] == [(1, "Travel")]


def test_v10_migration_is_idempotent(tmp_path):
    engine = _v10_database(tmp_path / "v10.db")
    init_schema(engine)
    with Session(engine) as session:
        session.add(Goal(title="New goal"))
        session.commit()

    init_schema(engine)

    with Session(engine) as session:
        assert [goal.title for goal in session.exec(select(Goal)).all()] == ["New goal"]
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def _habit_id(session: Session) -> int:
    return create_habit(session, "Read", RuleInput(frequency=HabitFrequency.EVERY_DAY)).id


def test_habit_support_points_at_exactly_one_quest_item(session):
    habit_id = _habit_id(session)
    goal = _add(session, Goal(title="Ship"))
    side_quest = _add(session, SideQuest(title="Trip"))
    session.add(HabitSupport(habit_id=habit_id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.add(HabitSupport(habit_id=habit_id, goal_id=goal.id, side_quest_id=side_quest.id))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    _add(session, HabitSupport(habit_id=habit_id, goal_id=goal.id))
    session.add(HabitSupport(habit_id=habit_id, goal_id=goal.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_habit_support_foreign_keys_are_restrict_and_indexed(engine):
    inspector = inspect(engine)
    indexed = {c for i in inspector.get_indexes("habit_support") for c in i["column_names"]}
    keys = inspector.get_foreign_keys("habit_support")
    assert {key["referred_table"] for key in keys} == {
        "habit",
        "ambition",
        "goal",
        "milestone",
        "side_quest",
        "chapter",
        "task",
    }
    for key in keys:
        assert key["options"].get("ondelete") == "RESTRICT", key
        assert set(key["constrained_columns"]) <= indexed, key
