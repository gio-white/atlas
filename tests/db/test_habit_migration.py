"""Schema 15: the habits rebuild migrates a schema 14 database (habits brief §11)."""

from datetime import date

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, select

from atlas.db import CURRENT_SCHEMA_VERSION, SchemaVersion, create_engine_for, init_schema
from atlas.db.models import Habit, HabitFreeze, HabitMark, HabitRule, Metric
from atlas.domain import HabitCheck, HabitFrequency, HabitSource, HabitThreshold, TimeOfDay

TODAY = date(2026, 8, 14)

V14_HABIT = """CREATE TABLE habit (id INTEGER NOT NULL, metric_id INTEGER NOT NULL,
 slug VARCHAR NOT NULL, name VARCHAR NOT NULL, period VARCHAR(5) NOT NULL,
 target_value FLOAT NOT NULL, comparator VARCHAR(8) NOT NULL, weekdays JSON,
 active_from DATE NOT NULL, active_to DATE, kind VARCHAR(8) NOT NULL,
 time_of_day VARCHAR(9) NOT NULL, archived_at DATETIME, PRIMARY KEY (id),
 FOREIGN KEY(metric_id) REFERENCES metric (id))"""
V14_BREAK = """CREATE TABLE habit_break (id INTEGER PRIMARY KEY,
 habit_id INTEGER NOT NULL REFERENCES habit(id), start_on DATE NOT NULL,
 end_on DATE NOT NULL, note VARCHAR, created_at DATETIME NOT NULL)"""


def _v14_database(path):
    """Today's schema with the habit tables put back as schema 14 had them."""
    engine = create_engine_for(path)
    SQLModel.metadata.create_all(engine)
    statements = [
        "PRAGMA foreign_keys=OFF",
        "DROP TABLE habit_rule",
        "DROP TABLE habit_mark",
        "DROP TABLE habit_freeze",
        "DROP TABLE habit",
        V14_HABIT,
        "CREATE UNIQUE INDEX ix_habit_slug ON habit (slug)",
        V14_BREAK,
        "INSERT INTO schema_version (id, version) VALUES (1, 14)",
        "INSERT INTO screen_category (id, slug, name, judgment) VALUES (1, 'social', 'Social',"
        " 'WASTE')",
    ]
    metrics = [
        (1, "meditated", "BOOL", "SUM", "MANUAL"),
        (2, "pushups", "COUNT", "SUM", "MANUAL"),
        (3, "runs", "COUNT", "SUM", "MANUAL"),
        (4, "slips", "COUNT", "SUM", "HABIT"),
        (5, "instagram", "DURATION", "SUM", "SCREEN"),
    ]
    for metric_id, slug, value_type, aggregation, origin in metrics:
        statements.append(
            "INSERT INTO metric (id, slug, name, value_type, aggregation, direction, origin)"
            f" VALUES ({metric_id}, '{slug}', '{slug}', '{value_type}', '{aggregation}',"
            f" 'NEUTRAL', '{origin}')"
        )
    statements.append(
        "INSERT INTO screen_app (id, slug, name, category_id, metric_id) VALUES"
        " (1, 'instagram', 'Instagram', 1, 5)"
    )
    habits = [
        (1, 1, "meditate", "Meditate", "DAY", 1, "AT_LEAST", None, "2026-08-10", None, "CHECK",
         "MORNING"),
        (2, 2, "pushups", "Pushups", "DAY", 20, "AT_LEAST", "[1, 2, 3, 4, 5]", "2026-08-10",
         None, "COUNT", "ANYTIME"),
        (3, 3, "runs", "Run", "WEEK", 3, "AT_LEAST", None, "2026-08-10", None, "COUNT",
         "ANYTIME"),
        (4, 4, "no-slips", "No slips", "DAY", 0, "AT_MOST", None, "2026-08-10", "2026-08-12",
         "QUIT", "EVENING"),
        (5, 5, "insta", "Instagram short", "DAY", 30, "AT_MOST", None, "2026-08-10", None,
         "DURATION", "EVENING"),
    ]  # fmt: skip
    for row in habits:
        values = ", ".join("NULL" if value is None else repr(value) for value in row)
        statements.append(
            "INSERT INTO habit (id, metric_id, slug, name, period, target_value, comparator,"
            " weekdays, active_from, active_to, kind, time_of_day) VALUES (" + values + ")"
        )
    entries = [
        (1, "2026-08-10", None, 1),
        (1, "2026-08-12", None, 1),
        (2, "2026-08-10", 25, None),
        (2, "2026-08-11", 10, None),
        (3, "2026-08-11", 1, None),
        (4, "2026-08-11", 1, None),
    ]
    for metric_id, day, value_num, value_bool in entries:
        num = "NULL" if value_num is None else value_num
        flag = "NULL" if value_bool is None else value_bool
        statements.append(
            "INSERT INTO entry (metric_id, occurred_on, value_num, value_bool, source,"
            f" created_at) VALUES ({metric_id}, '{day}', {num}, {flag}, 'MANUAL',"
            " '2026-08-12 10:00:00')"
        )
    statements.append(
        "INSERT INTO habit_break (habit_id, start_on, end_on, note, created_at) VALUES"
        " (1, '2026-08-11', '2026-08-11', 'Travel', '2026-08-10 10:00:00')"
    )
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return engine


def _rules(session: Session) -> dict[str, HabitRule]:
    habits = {habit.id: habit.slug for habit in session.exec(select(Habit)).all()}
    return {habits[rule.habit_id]: rule for rule in session.exec(select(HabitRule)).all()}


def _done(session: Session, slug: str) -> list[date]:
    habit = session.exec(select(Habit).where(Habit.slug == slug)).one()
    marks = session.exec(select(HabitMark).where(HabitMark.habit_id == habit.id)).all()
    return sorted(mark.day for mark in marks)


def test_schema_15_turns_each_habit_into_a_rule_and_its_done_days(tmp_path):
    engine = _v14_database(tmp_path / "v14.db")

    init_schema(engine, today=TODAY)

    inspector = inspect(engine)
    assert "habit_break" not in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("habit")}
    assert {"first_day", "time_of_day", "archived_at"} <= columns
    assert not {"metric_id", "kind", "period", "target_value"} & columns
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION
        rules = _rules(session)
        assert rules["meditate"].frequency == HabitFrequency.EVERY_DAY
        assert rules["pushups"].frequency == HabitFrequency.SPECIFIC_DAYS
        assert rules["pushups"].weekdays == [1, 2, 3, 4, 5]
        assert (rules["runs"].frequency, rules["runs"].times) == (HabitFrequency.TIMES_A_WEEK, 3)
        assert all(
            rule.check == HabitCheck.MANUAL for slug, rule in rules.items() if slug != "insta"
        )
        insta = rules["insta"]
        assert (insta.check, insta.source, insta.source_ref) == (
            HabitCheck.DATA,
            HabitSource.SCREEN_APP,
            "instagram",
        )
        assert (insta.threshold, insta.value) == (HabitThreshold.AT_MOST, 30)
        assert all(rule.starts_on == date(2026, 8, 10) for rule in rules.values())

        assert _done(session, "meditate") == [date(2026, 8, 10), date(2026, 8, 12)]
        assert _done(session, "pushups") == [date(2026, 8, 10)]
        assert _done(session, "runs") == [date(2026, 8, 11)]
        assert _done(session, "no-slips") == [date(2026, 8, 10), date(2026, 8, 12)]
        assert _done(session, "insta") == []

        habits = {habit.slug: habit for habit in session.exec(select(Habit)).all()}
        assert habits["meditate"].time_of_day == TimeOfDay.MORNING
        assert habits["meditate"].first_day == date(2026, 8, 10)
        assert habits["no-slips"].archived_at is not None
        assert habits["runs"].archived_at is None
        [freeze] = session.exec(select(HabitFreeze)).all()
        assert (freeze.habit_id, freeze.start_on, freeze.reason) == (
            habits["meditate"].id,
            date(2026, 8, 11),
            "Travel",
        )
        archived = {m.slug: m.archived_at is not None for m in session.exec(select(Metric))}
        assert archived == {
            "meditated": True,
            "pushups": True,
            "runs": True,
            "slips": True,
            "instagram": False,
        }
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []


def test_schema_15_runs_once(tmp_path):
    engine = _v14_database(tmp_path / "v14.db")
    init_schema(engine, today=TODAY)
    init_schema(engine, today=TODAY)

    with Session(engine) as session:
        assert len(session.exec(select(HabitRule)).all()) == 5
        assert len(session.exec(select(HabitFreeze)).all()) == 1
