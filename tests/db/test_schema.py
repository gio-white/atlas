from datetime import date

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from atlas.db import (
    CURRENT_SCHEMA_VERSION,
    Entry,
    Habit,
    HabitRule,
    LibraryTitle,
    LibraryTopic,
    Metric,
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
    HabitCheck,
    HabitFrequency,
    HabitSource,
    LibraryKind,
    LibraryStatus,
    MetricOrigin,
    Period,
    ScreenJudgment,
    Source,
    TimeOfDay,
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


def _metric(session: Session, slug: str = "pushups") -> Metric:
    metric = Metric(
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


@pytest.mark.parametrize("model", [Metric, Habit])
def test_slug_is_unique(session, model):
    metric = _metric(session)
    first = _row_for(model, slug="dup", metric=metric)
    session.add(first)
    session.commit()
    session.add(_row_for(model, slug="dup", metric=metric))

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

    metric = _metric(session, slug="instagram")
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


def test_library_slugs_are_unique(session):
    session.add(LibraryTopic(slug="physics", name="Physics"))
    session.commit()
    session.add(LibraryTopic(slug="physics", name="Other"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(
        LibraryTitle(
            slug="interstellar",
            name="Interstellar",
            kind=LibraryKind.FILM,
            status=LibraryStatus.QUEUED,
        )
    )
    session.commit()
    session.add(
        LibraryTitle(
            slug="interstellar",
            name="Other",
            kind=LibraryKind.BOOK,
            status=LibraryStatus.QUEUED,
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
    metric = _metric(session)
    day = date(2026, 8, 13)
    session.add(Entry(metric_id=metric.id, occurred_on=day, value_num=10, source=Source.CLI))
    session.add(Entry(metric_id=metric.id, occurred_on=day, value_num=20, source=Source.API))
    session.commit()

    rows = session.exec(select(Entry).where(Entry.metric_id == metric.id)).all()
    assert len(rows) == 2


def test_a_metric_is_manual_unless_told_otherwise_and_belongs_to_no_area(session, engine):
    metric = _metric(session)

    assert MetricOrigin(metric.origin) is MetricOrigin.MANUAL
    assert "area_id" not in {column["name"] for column in inspect(engine).get_columns("metric")}
    assert "area" not in inspect(engine).get_table_names()


def test_habit_rule_weekdays_round_trip_as_json_and_none_as_null(session, engine):
    habit = Habit(slug="weekday-runs", name="Weekday runs", first_day=date(2026, 8, 1))
    session.add(habit)
    session.commit()
    some_days = HabitRule(
        habit_id=habit.id,
        starts_on=date(2026, 8, 1),
        frequency=HabitFrequency.SPECIFIC_DAYS,
        weekdays=[1, 2, 3, 4, 5],
        check=HabitCheck.MANUAL,
    )
    every_day = HabitRule(
        habit_id=habit.id,
        starts_on=date(2026, 8, 10),
        frequency=HabitFrequency.EVERY_DAY,
        check=HabitCheck.MANUAL,
    )
    session.add_all([some_days, every_day])
    session.commit()
    session.refresh(some_days)

    assert some_days.weekdays == [1, 2, 3, 4, 5]
    with engine.connect() as connection:
        stored = connection.execute(
            text("SELECT weekdays FROM habit_rule WHERE starts_on = '2026-08-10'")
        ).scalar()
    assert stored is None


def test_a_manual_rule_cannot_carry_a_source(session):
    habit = Habit(slug="read", name="Read", first_day=date(2026, 8, 1))
    session.add(habit)
    session.commit()
    session.add(
        HabitRule(
            habit_id=habit.id,
            starts_on=date(2026, 8, 1),
            frequency=HabitFrequency.EVERY_DAY,
            check=HabitCheck.MANUAL,
            source=HabitSource.WAKE_TIME,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def _row_for(model, *, slug: str, metric: Metric):
    if model is Metric:
        return Metric(
            slug=slug,
            name=slug,
            value_type=ValueType.BOOL,
            aggregation=Aggregation.SUM,
            direction=Direction.NEUTRAL,
        )
    assert model is Habit
    return Habit(slug=slug, name=slug, first_day=date(2026, 8, 1))


def test_init_schema_adds_library_rating_and_link(tmp_path):
    engine = create_engine_for(tmp_path / "v8.db")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE entertainment_title ("
                "id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL UNIQUE, name VARCHAR NOT NULL, "
                "kind VARCHAR NOT NULL, creator VARCHAR, recommended_by VARCHAR, "
                "status VARCHAR NOT NULL, started_on DATE, finished_on DATE, progress VARCHAR, "
                "note VARCHAR, image_url VARCHAR, image_bytes BLOB, image_media_type VARCHAR, "
                "archived_at DATETIME, created_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        )
        connection.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 8)"))
        connection.execute(
            text(
                "INSERT INTO entertainment_title (slug, name, kind, status, created_at) "
                "VALUES ('dune', 'Dune', 'BOOK', 'QUEUED', '2026-08-01 12:00:00')"
            )
        )
    init_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("library_title")}
    assert {"rating", "link"} <= columns
    with Session(engine) as session:
        title = session.exec(select(LibraryTitle)).one()
        assert title.slug == "dune"
        assert title.rating is None
        assert title.link is None
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def test_init_schema_carries_a_v9_habit_through_to_rules(tmp_path):
    engine = create_engine_for(tmp_path / "v9.db")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE area (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL UNIQUE, "
                "name VARCHAR NOT NULL, description VARCHAR, archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE metric (id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL, "
                "slug VARCHAR NOT NULL UNIQUE, name VARCHAR NOT NULL, value_type VARCHAR NOT NULL,"
                " unit VARCHAR, aggregation VARCHAR NOT NULL, direction VARCHAR NOT NULL, "
                "archived_at DATETIME)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE habit (id INTEGER PRIMARY KEY, metric_id INTEGER NOT NULL, "
                "slug VARCHAR NOT NULL UNIQUE, name VARCHAR NOT NULL, period VARCHAR NOT NULL, "
                "target_value FLOAT NOT NULL, comparator VARCHAR NOT NULL, weekdays JSON, "
                "active_from DATE NOT NULL, active_to DATE)"
            )
        )
        connection.execute(
            text("CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)")
        )
        connection.execute(text("INSERT INTO schema_version (id, version) VALUES (1, 9)"))
        connection.execute(text("INSERT INTO area (id, slug, name) VALUES (1, 'health', 'Health')"))
        for metric_id, slug, value_type in (
            (1, "meditated", "BOOL"),
            (2, "pushups", "COUNT"),
            (3, "deep-work", "DURATION"),
        ):
            connection.execute(
                text(
                    "INSERT INTO metric (id, area_id, slug, name, value_type, aggregation, "
                    "direction) VALUES (:id, 1, :slug, :slug, :value_type, 'SUM', "
                    "'HIGHER_IS_BETTER')"
                ),
                {"id": metric_id, "slug": slug, "value_type": value_type},
            )
            connection.execute(
                text(
                    "INSERT INTO habit (metric_id, slug, name, period, target_value, comparator,"
                    " active_from) VALUES (:id, :slug, :slug, 'DAY', 1, 'AT_LEAST', '2026-08-01')"
                ),
                {"id": metric_id, "slug": slug},
            )
    init_schema(engine)

    tables = set(inspect(engine).get_table_names())
    assert "habit_break" not in tables
    columns = {column["name"] for column in inspect(engine).get_columns("habit")}
    assert {"first_day", "time_of_day", "archived_at"} <= columns
    assert not {"goal_id", "kind", "metric_id"} & columns
    with Session(engine) as session:
        assert {habit.slug for habit in session.exec(select(Habit)).all()} == {
            "meditated",
            "pushups",
            "deep-work",
        }
        rules = session.exec(select(HabitRule)).all()
        assert {(rule.frequency, rule.check) for rule in rules} == {
            (HabitFrequency.EVERY_DAY, HabitCheck.MANUAL)
        }
        habit = session.exec(select(Habit).where(Habit.slug == "pushups")).one()
        assert habit.time_of_day is TimeOfDay.ANYTIME
        assert habit.archived_at is None
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION


def _v11_database_with_areas(path):
    """A schema 11 database: metrics belong to areas, and nothing says where a metric came from."""
    engine = create_engine_for(path)
    statements = [
        "CREATE TABLE area (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL, name VARCHAR NOT NULL,"
        " description VARCHAR, archived_at DATETIME)",
        "CREATE UNIQUE INDEX ix_area_slug ON area (slug)",
        "CREATE TABLE metric (id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL REFERENCES area(id),"
        " slug VARCHAR NOT NULL, name VARCHAR NOT NULL, value_type VARCHAR NOT NULL,"
        " unit VARCHAR, aggregation VARCHAR NOT NULL, direction VARCHAR NOT NULL,"
        " archived_at DATETIME)",
        "CREATE UNIQUE INDEX ix_metric_slug ON metric (slug)",
        "CREATE TABLE entry (id INTEGER PRIMARY KEY,"
        " metric_id INTEGER NOT NULL REFERENCES metric(id), occurred_on DATE NOT NULL,"
        " occurred_at DATETIME, value_num FLOAT, value_bool BOOLEAN, value_text VARCHAR,"
        " note VARCHAR, source VARCHAR NOT NULL, created_at DATETIME NOT NULL)",
        "CREATE TABLE habit (id INTEGER PRIMARY KEY,"
        " metric_id INTEGER NOT NULL REFERENCES metric(id), slug VARCHAR NOT NULL,"
        " name VARCHAR NOT NULL, period VARCHAR NOT NULL, target_value FLOAT NOT NULL,"
        " comparator VARCHAR NOT NULL, weekdays JSON, active_from DATE NOT NULL, active_to DATE,"
        " kind VARCHAR NOT NULL, time_of_day VARCHAR NOT NULL, archived_at DATETIME)",
        "CREATE UNIQUE INDEX ix_habit_slug ON habit (slug)",
        "CREATE TABLE screen_category (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL,"
        " name VARCHAR NOT NULL, judgment VARCHAR NOT NULL, archived_at DATETIME)",
        "CREATE TABLE screen_app (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL,"
        " name VARCHAR NOT NULL, category_id INTEGER NOT NULL REFERENCES screen_category(id),"
        " metric_id INTEGER NOT NULL REFERENCES metric(id), archived_at DATETIME)",
        "CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER NOT NULL)",
        "INSERT INTO schema_version VALUES (1, 11)",
        "INSERT INTO area VALUES (1, 'health', 'Health', NULL, NULL)",
        "INSERT INTO area VALUES (2, 'habits', 'Habits', NULL, NULL)",
        "INSERT INTO area VALUES (3, 'screen', 'Screen', NULL, NULL)",
        "INSERT INTO area VALUES (4, 'life', 'Life', NULL, NULL)",
        "INSERT INTO area VALUES (5, 'old', 'Old', NULL, '2026-05-01 00:00:00')",
        "INSERT INTO metric VALUES (1, 1, 'pushups', 'Pushups', 'COUNT', 'reps', 'SUM',"
        " 'HIGHER_IS_BETTER', NULL)",
        "INSERT INTO metric VALUES (2, 2, 'meditate', 'Meditate', 'BOOL', NULL, 'SUM',"
        " 'HIGHER_IS_BETTER', NULL)",
        "INSERT INTO metric VALUES (3, 3, 'instagram', 'Instagram', 'DURATION', 'min', 'SUM',"
        " 'LOWER_IS_BETTER', NULL)",
        "INSERT INTO metric VALUES (4, 4, 'journal', 'Journal', 'TEXT', NULL, 'LAST',"
        " 'NEUTRAL', NULL)",
        "INSERT INTO metric VALUES (5, 5, 'retired', 'Retired', 'COUNT', NULL, 'SUM',"
        " 'NEUTRAL', NULL)",
        "INSERT INTO metric VALUES (6, 5, 'retired-earlier', 'Retired earlier', 'COUNT', NULL,"
        " 'SUM', 'NEUTRAL', '2026-01-01 00:00:00')",
        # A screen app whose metric was filed under a user's own area still counts as screen.
        "INSERT INTO metric VALUES (7, 1, 'youtube', 'YouTube', 'DURATION', 'min', 'SUM',"
        " 'LOWER_IS_BETTER', NULL)",
        "INSERT INTO screen_category VALUES (1, 'social', 'Social', 'WASTE', NULL)",
        "INSERT INTO screen_app VALUES (1, 'instagram', 'Instagram', 1, 3, NULL)",
        "INSERT INTO screen_app VALUES (2, 'youtube', 'YouTube', 1, 7, NULL)",
        "INSERT INTO entry VALUES (1, 1, '2026-08-13', NULL, 40, NULL, NULL, 'morning', 'CLI',"
        " '2026-08-13 08:00:00')",
        "INSERT INTO habit VALUES (1, 2, 'meditate', 'Meditate', 'DAY', 1, 'AT_LEAST', NULL,"
        " '2026-08-01', NULL, 'CHECK', 'MORNING', NULL)",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return engine


def test_init_schema_replaces_areas_with_metric_origins(tmp_path):
    engine = _v11_database_with_areas(tmp_path / "v11.db")

    init_schema(engine)

    assert CURRENT_SCHEMA_VERSION == 15
    inspector = inspect(engine)
    assert "area" not in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("metric")}
    assert "area_id" not in columns
    assert "origin" in columns
    assert any(
        index["unique"] and index["column_names"] == ["slug"]
        for index in inspector.get_indexes("metric")
    )
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION
        origins = {
            metric.slug: MetricOrigin(metric.origin)
            for metric in session.exec(select(Metric)).all()
        }
        assert origins == {
            "pushups": MetricOrigin.MANUAL,
            "meditate": MetricOrigin.HABIT,
            "instagram": MetricOrigin.SCREEN,
            "journal": MetricOrigin.JOURNAL,
            "retired": MetricOrigin.MANUAL,
            "retired-earlier": MetricOrigin.MANUAL,
            "youtube": MetricOrigin.SCREEN,
        }


def test_the_area_migration_keeps_ids_values_and_what_points_at_metrics(tmp_path):
    engine = _v11_database_with_areas(tmp_path / "v11.db")

    init_schema(engine)

    with Session(engine) as session:
        pushups = session.exec(select(Metric).where(Metric.slug == "pushups")).one()
        assert (pushups.id, pushups.name, pushups.unit) == (1, "Pushups", "reps")
        assert pushups.value_type is ValueType.COUNT
        assert pushups.aggregation is Aggregation.SUM
        assert pushups.direction is Direction.HIGHER_IS_BETTER
        entry = session.exec(select(Entry)).one()
        assert (entry.metric_id, entry.value_num, entry.note) == (1, 40.0, "morning")
        habit = session.exec(select(Habit)).one()
        assert habit.slug == "meditate"
        # Schema 15 archives the metric a habit read; its entries stay.
        assert session.get(Metric, 2).archived_at is not None
        apps = {app.slug: app.metric_id for app in session.exec(select(ScreenApp)).all()}
        assert apps == {"instagram": 3, "youtube": 7}
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_the_area_migration_archives_metrics_of_an_archived_area(tmp_path):
    engine = _v11_database_with_areas(tmp_path / "v11.db")

    init_schema(engine)

    with Session(engine) as session:
        archived = {
            metric.slug: metric.archived_at for metric in session.exec(select(Metric)).all()
        }
    assert archived["pushups"] is None
    assert archived["retired"] is not None
    assert (archived["retired"].year, archived["retired"].month) == (2026, 5)
    assert (archived["retired-earlier"].year, archived["retired-earlier"].month) == (2026, 1)


def test_the_area_migration_runs_once(tmp_path):
    engine = _v11_database_with_areas(tmp_path / "v11.db")
    init_schema(engine)
    with Session(engine) as session:
        session.add(
            Metric(
                slug="weight",
                name="Weight",
                value_type=ValueType.QUANTITY,
                aggregation=Aggregation.LAST,
                direction=Direction.LOWER_IS_BETTER,
            )
        )
        session.commit()

    init_schema(engine)

    with Session(engine) as session:
        assert len(session.exec(select(Metric)).all()) == 8


def test_init_schema_renames_entertainment_tables_to_library(tmp_path):
    engine = create_engine_for(tmp_path / "v12.db")
    with engine.begin() as connection:
        for statement in (
            "CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER)",
            "INSERT INTO schema_version (id, version) VALUES (1, 12)",
            "CREATE TABLE entertainment_topic (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL "
            "UNIQUE, name VARCHAR NOT NULL, archived_at DATETIME)",
            "CREATE INDEX ix_entertainment_topic_slug ON entertainment_topic (slug)",
            "CREATE TABLE entertainment_title (id INTEGER PRIMARY KEY, slug VARCHAR NOT NULL "
            "UNIQUE, name VARCHAR NOT NULL, kind VARCHAR NOT NULL, creator VARCHAR, "
            "recommended_by VARCHAR, status VARCHAR NOT NULL, started_on DATE, finished_on DATE, "
            "progress VARCHAR, note VARCHAR, rating INTEGER, link VARCHAR, image_url VARCHAR, "
            "image_bytes BLOB, image_media_type VARCHAR, archived_at DATETIME, "
            "created_at DATETIME NOT NULL)",
            "CREATE INDEX ix_entertainment_title_slug ON entertainment_title (slug)",
            "CREATE TABLE entertainment_title_topic ("
            "title_id INTEGER NOT NULL REFERENCES entertainment_title (id), "
            "topic_id INTEGER NOT NULL REFERENCES entertainment_topic (id), "
            "PRIMARY KEY (title_id, topic_id))",
            "INSERT INTO entertainment_topic (id, slug, name) VALUES (7, 'jazz', 'Jazz')",
            "INSERT INTO entertainment_title (id, slug, name, kind, status, created_at) "
            "VALUES (3, 'kind-of-blue', 'Kind of Blue', 'MUSIC', 'DONE', '2026-08-01 12:00:00')",
            "INSERT INTO entertainment_title_topic (title_id, topic_id) VALUES (3, 7)",
        ):
            connection.execute(text(statement))

    init_schema(engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"library_topic", "library_title", "library_title_topic"} <= tables
    assert not {name for name in tables if name.startswith("entertainment_")}
    assert {index["name"] for index in inspector.get_indexes("library_title")} >= {
        "ix_library_title_slug"
    }
    links = inspector.get_foreign_keys("library_title_topic")
    assert {link["referred_table"] for link in links} == {"library_title", "library_topic"}
    with Session(engine) as session:
        title = session.exec(select(LibraryTitle)).one()
        assert (title.id, title.slug, title.status) == (3, "kind-of-blue", LibraryStatus.DONE)
        assert session.exec(select(LibraryTopic)).one().id == 7
        assert session.get(SchemaVersion, 1).version == CURRENT_SCHEMA_VERSION
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
