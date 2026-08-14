from datetime import date

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from atlas.db import (
    CURRENT_SCHEMA_VERSION,
    Area,
    EntertainmentTitle,
    EntertainmentTopic,
    Entry,
    Goal,
    Habit,
    Metric,
    Milestone,
    SchemaVersion,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    ScreenDevice,
    ScreenSession,
    create_engine_for,
    create_memory_engine,
    init_db,
    init_schema,
    make_session_factory,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    EntertainmentKind,
    EntertainmentStatus,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    ScreenJudgment,
    Source,
    ValueType,
)


@pytest.fixture
def engine():
    memory = create_memory_engine()
    init_schema(memory)
    return memory


@pytest.fixture
def session(engine):
    factory = make_session_factory(engine)
    with factory() as db_session:
        yield db_session


def _area(session: Session, slug: str = "health") -> Area:
    area = Area(slug=slug, name=slug.title())
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


def _metric(session: Session, area: Area, slug: str = "pushups") -> Metric:
    metric = Metric(
        area_id=area.id,
        slug=slug,
        name=slug.title(),
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def test_init_schema_records_version(engine):
    with Session(engine) as session:
        row = session.get(SchemaVersion, 1)
        assert row is not None
        assert row.version == CURRENT_SCHEMA_VERSION


def test_init_schema_is_idempotent(engine):
    init_schema(engine)
    with Session(engine) as session:
        rows = session.exec(select(SchemaVersion)).all()
        assert len(rows) == 1
        assert rows[0].version == CURRENT_SCHEMA_VERSION


def test_init_db_creates_parent_directory_and_file(tmp_path):
    db_path = tmp_path / "nested" / "atlas.db"
    engine = init_db(db_path)

    assert db_path.exists()
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1) is not None


def test_entry_is_indexed_on_metric_and_occurred_on(engine):
    indexes = inspect(engine).get_indexes("entry")
    column_sets = {tuple(index["column_names"]) for index in indexes}

    assert ("metric_id", "occurred_on") in column_sets


@pytest.mark.parametrize("model", [Area, Metric, Habit, Goal])
def test_slug_is_unique(session, model):
    area = _area(session)
    metric = _metric(session, area)
    first = _row_for(model, slug="dup", area=area, metric=metric)
    session.add(first)
    session.commit()
    session.add(_row_for(model, slug="dup", area=area, metric=metric))

    with pytest.raises(IntegrityError):
        session.commit()


def test_screen_slugs_are_unique(session):
    category = ScreenCategory(
        slug="entertainment",
        name="Entertainment",
        judgment=ScreenJudgment.WASTE,
    )
    session.add(category)
    session.commit()
    session.add(ScreenCategory(slug="entertainment", name="Other", judgment=ScreenJudgment.NEUTRAL))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    area = _area(session, slug="screen")
    metric = _metric(session, area, slug="instagram")
    session.add(
        ScreenApp(
            slug="instagram",
            name="Instagram",
            category_id=category.id,
            metric_id=metric.id,
        )
    )
    session.commit()
    session.add(
        ScreenApp(
            slug="instagram",
            name="Again",
            category_id=category.id,
            metric_id=metric.id,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(
        ScreenBudget(
            slug="waste-cap",
            name="Waste cap",
            target_kind="judgment",
            target_slug="waste",
            period=Period.DAY,
            target_value=90.0,
            comparator=Comparator.AT_MOST,
            active_from=date(2026, 8, 1),
        )
    )
    session.commit()
    session.add(
        ScreenBudget(
            slug="waste-cap",
            name="Again",
            target_kind="judgment",
            target_slug="waste",
            period=Period.DAY,
            target_value=60.0,
            comparator=Comparator.AT_MOST,
            active_from=date(2026, 8, 1),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_entertainment_slugs_are_unique(session):
    session.add(EntertainmentTopic(slug="physics", name="Physics"))
    session.commit()
    session.add(EntertainmentTopic(slug="physics", name="Other"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(
        EntertainmentTitle(
            slug="interstellar",
            name="Interstellar",
            kind=EntertainmentKind.FILM,
            status=EntertainmentStatus.QUEUED,
        )
    )
    session.commit()
    session.add(
        EntertainmentTitle(
            slug="interstellar",
            name="Other",
            kind=EntertainmentKind.BOOK,
            status=EntertainmentStatus.QUEUED,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_screen_device_slug_is_unique(session):
    session.add(ScreenDevice(slug="iphone", name="iPhone"))
    session.commit()
    session.add(ScreenDevice(slug="iphone", name="Again"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_screen_session_is_indexed_on_app_and_occurred_on(engine):
    indexes = inspect(engine).get_indexes("screen_session")
    column_sets = {tuple(index["column_names"]) for index in indexes}
    assert ("app_id", "occurred_on") in column_sets


def test_init_schema_backfills_sessions_from_screen_app_entries(tmp_path):
    engine = create_engine_for(tmp_path / "v4.db")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE area ("
                "id INTEGER PRIMARY KEY, slug VARCHAR UNIQUE, name VARCHAR, "
                "description TEXT, archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE metric ("
                "id INTEGER PRIMARY KEY, area_id INTEGER, slug VARCHAR UNIQUE, name VARCHAR, "
                "value_type VARCHAR, unit VARCHAR, aggregation VARCHAR, direction VARCHAR, "
                "archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE entry ("
                "id INTEGER PRIMARY KEY, metric_id INTEGER, occurred_on DATE, "
                "occurred_at DATETIME, value_num FLOAT, value_bool BOOLEAN, "
                "value_text TEXT, note TEXT, source VARCHAR, created_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE screen_category ("
                "id INTEGER PRIMARY KEY, slug VARCHAR UNIQUE, name VARCHAR, "
                "judgment VARCHAR, archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE screen_app ("
                "id INTEGER PRIMARY KEY, slug VARCHAR UNIQUE, name VARCHAR, "
                "category_id INTEGER, metric_id INTEGER UNIQUE, archived_at DATETIME)"
            )
        )
        connection.execute(
            text("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        )
        connection.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 4)"))
        connection.execute(text("INSERT INTO area (id, slug, name) VALUES (1, 'screen', 'Screen')"))
        connection.execute(
            text(
                "INSERT INTO metric (id, area_id, slug, name, value_type, aggregation, direction) "
                "VALUES (1, 1, 'instagram', 'Instagram', 'DURATION', 'SUM', 'LOWER_IS_BETTER')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO screen_category (id, slug, name, judgment) "
                "VALUES (1, 'entertainment', 'Entertainment', 'WASTE')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO screen_app (id, slug, name, category_id, metric_id) "
                "VALUES (1, 'instagram', 'Instagram', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO entry (id, metric_id, occurred_on, value_num, source, created_at) "
                "VALUES (1, 1, '2026-08-14', 30.0, 'CLI', '2026-08-14T12:00:00+00:00')"
            )
        )
    init_schema(engine)
    with Session(engine) as session:
        rows = session.exec(select(ScreenSession)).all()
        assert len(rows) == 1
        assert rows[0].minutes == 30.0
        assert rows[0].entry_id == 1
        assert rows[0].started_at is None
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def test_multiple_entries_per_day_are_allowed(session):
    metric = _metric(session, _area(session))
    day = date(2026, 8, 13)
    session.add(Entry(metric_id=metric.id, occurred_on=day, value_num=10, source=Source.CLI))
    session.add(Entry(metric_id=metric.id, occurred_on=day, value_num=20, source=Source.API))
    session.commit()

    rows = session.exec(select(Entry).where(Entry.metric_id == metric.id)).all()
    assert len(rows) == 2


def test_foreign_key_rejects_unknown_area(session):
    session.add(
        Metric(
            area_id=999,
            slug="orphan",
            name="Orphan",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
            direction=Direction.NEUTRAL,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_habit_weekdays_round_trip_as_json(session):
    metric = _metric(session, _area(session))
    habit = Habit(
        metric_id=metric.id,
        slug="weekday-runs",
        name="Weekday runs",
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        weekdays=[1, 2, 3, 4, 5],
        active_from=date(2026, 8, 1),
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)

    assert habit.weekdays == [1, 2, 3, 4, 5]


def test_goal_and_milestone_persist(session):
    area = _area(session)
    metric = _metric(session, area, slug="weight")
    goal = Goal(
        area_id=area.id,
        slug="bodyweight-75",
        name="Bodyweight 75kg",
        kind=GoalKind.METRIC_TARGET,
        metric_id=metric.id,
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 1),
        status=GoalStatus.ACTIVE,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    session.add(Milestone(goal_id=goal.id, name="Hit 78kg"))
    session.commit()

    stored = session.exec(select(Milestone).where(Milestone.goal_id == goal.id)).one()
    assert stored.name == "Hit 78kg"
    assert stored.done_at is None


def test_init_schema_migrates_v3_goal_hierarchy_columns(tmp_path):
    engine = create_engine_for(tmp_path / "v3.db")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE area ("
                "id INTEGER PRIMARY KEY, slug VARCHAR UNIQUE, name VARCHAR, "
                "description TEXT, archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE goal ("
                "id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL, slug VARCHAR UNIQUE, "
                "name VARCHAR, kind VARCHAR, metric_id INTEGER, target_value FLOAT, "
                "comparator VARCHAR, baseline_value FLOAT, measure VARCHAR, "
                "start_on DATE, due_on DATE, status VARCHAR, achieved_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE task ("
                "id INTEGER PRIMARY KEY, title VARCHAR, bucket VARCHAR, due_on DATE, "
                "due_at DATETIME, priority VARCHAR, done_at DATETIME, created_at DATETIME)"
            )
        )
        connection.execute(
            text("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        )
        connection.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 3)"))
        connection.execute(text("INSERT INTO area (id, slug, name) VALUES (1, 'health', 'Health')"))
        connection.execute(
            text(
                "INSERT INTO goal (id, area_id, slug, name, kind, start_on, due_on, status) "
                "VALUES (1, 1, 'year-goal', 'Year', 'milestone',"
                " '2026-01-01', '2027-01-01', 'active')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO goal (id, area_id, slug, name, kind, start_on, due_on, status) "
                "VALUES (2, 1, 'week-goal', 'Week', 'milestone',"
                " '2026-08-10', '2026-08-16', 'active')"
            )
        )
    init_schema(engine)

    goal_columns = {column["name"] for column in inspect(engine).get_columns("goal")}
    task_columns = {column["name"] for column in inspect(engine).get_columns("task")}
    assert {"horizon", "parent_id", "description"} <= goal_columns
    assert "goal_id" in task_columns
    with engine.connect() as connection:
        horizons = {
            row.slug: row.horizon
            for row in connection.execute(text("SELECT slug, horizon FROM goal")).all()
        }
    assert horizons["year-goal"] == "long"
    assert horizons["week-goal"] == "short"
    area_column = next(
        column for column in inspect(engine).get_columns("goal") if column["name"] == "area_id"
    )
    assert area_column["nullable"] is True
    with engine.connect() as connection:
        year = connection.execute(text("SELECT area_id FROM goal WHERE slug = 'year-goal'")).one()
        assert year.area_id == 1
        connection.execute(text("UPDATE goal SET area_id = NULL WHERE slug = 'year-goal'"))
        connection.commit()
        cleared = connection.execute(
            text("SELECT area_id FROM goal WHERE slug = 'year-goal'")
        ).one()
        assert cleared.area_id is None
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def test_goal_can_omit_area(session):
    goal = Goal(
        slug="north",
        name="North",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
        status=GoalStatus.ACTIVE,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    assert goal.area_id is None


def test_init_schema_migrates_v5_nullable_goal_area(tmp_path):
    engine = create_engine_for(tmp_path / "v5.db")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE area ("
                "id INTEGER PRIMARY KEY, slug VARCHAR UNIQUE, name VARCHAR, "
                "description TEXT, archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE goal ("
                "id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL, slug VARCHAR UNIQUE, "
                "name VARCHAR, kind VARCHAR, metric_id INTEGER, target_value FLOAT, "
                "comparator VARCHAR, baseline_value FLOAT, measure VARCHAR, "
                "start_on DATE, due_on DATE, horizon VARCHAR NOT NULL, parent_id INTEGER, "
                "description TEXT, status VARCHAR, achieved_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE milestone ("
                "id INTEGER PRIMARY KEY, goal_id INTEGER NOT NULL, name VARCHAR, "
                "due_on DATE, done_at DATETIME, "
                "FOREIGN KEY(goal_id) REFERENCES goal(id))"
            )
        )
        connection.execute(
            text("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        )
        connection.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 5)"))
        connection.execute(text("INSERT INTO area (id, slug, name) VALUES (1, 'health', 'Health')"))
        connection.execute(
            text(
                "INSERT INTO goal (id, area_id, slug, name, kind, start_on, due_on, "
                "horizon, status) VALUES (1, 1, 'north', 'North', 'milestone',"
                " '2026-01-01', '2028-01-01', 'long', 'active')"
            )
        )
        connection.execute(
            text("INSERT INTO milestone (id, goal_id, name) VALUES (1, 1, 'keep-going')")
        )
    init_schema(engine)

    area_column = next(
        column for column in inspect(engine).get_columns("goal") if column["name"] == "area_id"
    )
    assert area_column["nullable"] is True
    with engine.connect() as connection:
        goal = connection.execute(text("SELECT id, area_id FROM goal WHERE slug = 'north'")).one()
        assert goal.area_id == 1
        milestone = connection.execute(text("SELECT goal_id FROM milestone")).one()
        assert milestone.goal_id == goal.id
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def _row_for(model, *, slug: str, area: Area, metric: Metric):
    if model is Area:
        return Area(slug=slug, name=slug)
    if model is Metric:
        return Metric(
            area_id=area.id,
            slug=slug,
            name=slug,
            value_type=ValueType.BOOL,
            aggregation=Aggregation.SUM,
            direction=Direction.NEUTRAL,
        )
    if model is Habit:
        return Habit(
            metric_id=metric.id,
            slug=slug,
            name=slug,
            period=Period.DAY,
            target_value=1.0,
            comparator=Comparator.AT_LEAST,
            active_from=date(2026, 8, 1),
        )
    return Goal(
        area_id=area.id,
        slug=slug,
        name=slug,
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
    )
