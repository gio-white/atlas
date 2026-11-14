from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Connection, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlmodel import Session, SQLModel, col, create_engine, select

from atlas.db.models import Entry, Habit, Metric, SchemaVersion, ScreenApp, ScreenSession
from atlas.domain import MetricOrigin

CURRENT_SCHEMA_VERSION = 13

# Tables of the goal/milestone/task model that schema 11 replaced, keyed by a column only the
# old shape has, so the drop is idempotent and never touches the new quest tables.
_LEGACY_TABLE_MARKERS = (("task", "bucket"), ("milestone", "name"), ("goal", "slug"))

# The Library's tables before schema 13 renamed them.
_ENTERTAINMENT_TABLES = ("entertainment_topic", "entertainment_title", "entertainment_title_topic")


def create_engine_for(db_path: Path) -> Engine:
    path = db_path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    _enable_sqlite_foreign_keys(engine)
    return engine


def create_memory_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _enable_sqlite_foreign_keys(engine)
    return engine


def make_session_factory(engine: Engine) -> Callable[[], Session]:
    def factory() -> Session:
        return Session(engine)

    return factory


def init_schema(engine: Engine) -> None:
    previous = _stored_version(engine)
    if previous is not None and previous < 11:
        _drop_legacy_goal_tables(engine)
    if previous is not None and previous < 13:
        # Before create_all, which would otherwise make empty library tables beside the old ones.
        _rename_entertainment_to_library(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        row = session.get(SchemaVersion, 1)
        if previous is not None and previous < CURRENT_SCHEMA_VERSION:
            if previous < 5:
                _backfill_screen_sessions(engine)
            if previous < 9:
                _add_library_rating_and_link(engine)
            if previous < 10:
                _add_habit_kind_and_schedule(engine)
            if previous < 11:
                _drop_habit_goal_link(engine)
            if previous < 12:
                _replace_areas_with_metric_origin(engine)
            session.expire_all()
            row = session.get(SchemaVersion, 1)
        if row is None:
            session.add(SchemaVersion(id=1, version=CURRENT_SCHEMA_VERSION))
        elif row.version < CURRENT_SCHEMA_VERSION:
            row.version = CURRENT_SCHEMA_VERSION
            session.add(row)
        session.commit()


def init_db(db_path: Path) -> Engine:
    engine = create_engine_for(db_path)
    init_schema(engine)
    return engine


def _stored_version(engine: Engine) -> int | None:
    if "schema_version" not in inspect(engine).get_table_names():
        return None
    with engine.connect() as connection:
        return connection.execute(text("SELECT version FROM schema_version WHERE id = 1")).scalar()


def _drop_legacy_goal_tables(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    legacy = [
        table
        for table, marker in _LEGACY_TABLE_MARKERS
        if table in tables and marker in {column["name"] for column in inspector.get_columns(table)}
    ]
    if not legacy:
        return

    def drop(connection: Connection) -> None:
        for table in legacy:
            connection.execute(text(f"DROP TABLE {table}"))

    _without_foreign_keys(engine, drop)


def _drop_habit_goal_link(engine: Engine) -> None:
    inspector = inspect(engine)
    if "habit" not in inspector.get_table_names():
        return
    old_columns = [column["name"] for column in inspector.get_columns("habit")]
    if "goal_id" not in old_columns:
        return
    kept = [column.name for column in Habit.__table__.columns if column.name in old_columns]
    quoted = ", ".join(kept)

    def rebuild(connection: Connection) -> None:
        create = str(CreateTable(Habit.__table__).compile(connection))
        connection.execute(
            text(create.replace("CREATE TABLE habit ", "CREATE TABLE habit__new ", 1))
        )
        connection.execute(text(f"INSERT INTO habit__new ({quoted}) SELECT {quoted} FROM habit"))
        connection.execute(text("DROP TABLE habit"))
        connection.execute(text("ALTER TABLE habit__new RENAME TO habit"))
        for index in Habit.__table__.indexes:
            connection.execute(CreateIndex(index, if_not_exists=True))

    _without_foreign_keys(engine, rebuild)


def _replace_areas_with_metric_origin(engine: Engine) -> None:
    """Schema 12: areas are gone. Each metric keeps what its area used to say about it.

    A metric in the internal `habits` or `screen` area (or backing a screen app) becomes a
    habit-made or screen metric, the `journal` metric becomes the journal one, and the rest
    are manual. A metric in an archived area was treated as archived, so it becomes archived.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "metric" not in tables:
        return
    old_columns = {column["name"] for column in inspector.get_columns("metric")}
    if "area_id" not in old_columns:
        return
    has_areas = "area" in tables
    kept = [
        column.name
        for column in Metric.__table__.columns
        if column.name in old_columns and column.name != "archived_at"
    ]
    screen_metric = (
        "m.id IN (SELECT metric_id FROM screen_app WHERE metric_id IS NOT NULL)"
        if "screen_app" in tables
        else "0"
    )
    area_is = (lambda slug: f"a.slug = '{slug}'") if has_areas else (lambda slug: "0")
    origin = (
        "CASE"
        f" WHEN {screen_metric} OR {area_is('screen')} THEN '{MetricOrigin.SCREEN.name}'"
        f" WHEN m.slug = 'journal' THEN '{MetricOrigin.JOURNAL.name}'"
        f" WHEN {area_is('habits')} THEN '{MetricOrigin.HABIT.name}'"
        f" ELSE '{MetricOrigin.MANUAL.name}' END"
    )
    archived_at = "COALESCE(m.archived_at, a.archived_at)" if has_areas else "m.archived_at"
    source = "metric m LEFT JOIN area a ON a.id = m.area_id" if has_areas else "metric m"
    columns = ", ".join(kept)
    selected = ", ".join(f"m.{name}" for name in kept)

    def rebuild(connection: Connection) -> None:
        create = str(CreateTable(Metric.__table__).compile(connection))
        connection.execute(
            text(create.replace("CREATE TABLE metric ", "CREATE TABLE metric__new ", 1))
        )
        connection.execute(
            text(
                f"INSERT INTO metric__new ({columns}, archived_at, origin) "
                f"SELECT {selected}, {archived_at}, {origin} FROM {source}"
            )
        )
        connection.execute(text("DROP TABLE metric"))
        connection.execute(text("ALTER TABLE metric__new RENAME TO metric"))
        for index in Metric.__table__.indexes:
            connection.execute(CreateIndex(index, if_not_exists=True))
        if has_areas:
            connection.execute(text("DROP TABLE area"))

    _without_foreign_keys(engine, rebuild)


def _without_foreign_keys(engine: Engine, work: Callable[[Connection], None]) -> None:
    """Run `work` in one transaction with SQLite foreign keys off (the table-rebuild recipe).

    The pragma is a no-op inside a transaction, so it is switched on an autocommit connection
    before BEGIN and restored after COMMIT or ROLLBACK.
    """
    with engine.connect() as connection:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text("BEGIN"))
        try:
            work(connection)
            connection.execute(text("COMMIT"))
        except Exception:
            connection.execute(text("ROLLBACK"))
            raise
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))


def _backfill_screen_sessions(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "screen_session" not in tables or "screen_app" not in tables or "entry" not in tables:
        return
    with Session(engine) as session:
        apps = list(session.exec(select(ScreenApp)).all())
        metric_to_app = {app.metric_id: app for app in apps if app.metric_id is not None}
        if not metric_to_app:
            return
        linked = {
            row.entry_id
            for row in session.exec(select(ScreenSession)).all()
            if row.entry_id is not None
        }
        entries = session.exec(
            select(Entry).where(col(Entry.metric_id).in_(list(metric_to_app)))
        ).all()
        for entry in entries:
            if entry.id is None or entry.id in linked:
                continue
            if entry.value_num is None or entry.value_num <= 0:
                continue
            app = metric_to_app[entry.metric_id]
            session.add(
                ScreenSession(
                    app_id=app.id,
                    minutes=entry.value_num,
                    occurred_on=entry.occurred_on,
                    note=entry.note,
                    source=entry.source,
                    created_at=entry.created_at,
                    entry_id=entry.id,
                )
            )
        session.commit()


def _rename_entertainment_to_library(engine: Engine) -> None:
    """Schema 13: the `entertainment_*` tables become `library_*`, rows and ids untouched.

    SQLite rewrites the foreign keys that point at a renamed table; the indexes keep their old
    names, so each is recreated under the new one.
    """
    tables = set(inspect(engine).get_table_names())
    renames = [
        (old, old.replace("entertainment_", "library_", 1))
        for old in _ENTERTAINMENT_TABLES
        if old in tables and old.replace("entertainment_", "library_", 1) not in tables
    ]
    if not renames:
        return

    def rename(connection: Connection) -> None:
        for old, new in renames:
            connection.execute(text(f"ALTER TABLE {old} RENAME TO {new}"))
        indexes = connection.execute(
            text(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type = 'index' AND name LIKE 'ix_entertainment_%' AND sql IS NOT NULL"
            )
        ).all()
        for name, sql in indexes:
            connection.execute(text(f"DROP INDEX {name}"))
            connection.execute(text(sql.replace("entertainment_", "library_")))

    _without_foreign_keys(engine, rename)


def _add_library_rating_and_link(engine: Engine) -> None:
    inspector = inspect(engine)
    if "library_title" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("library_title")}
    with engine.begin() as connection:
        if "rating" not in columns:
            connection.execute(text("ALTER TABLE library_title ADD COLUMN rating INTEGER"))
        if "link" not in columns:
            connection.execute(text("ALTER TABLE library_title ADD COLUMN link VARCHAR"))


def _add_habit_kind_and_schedule(engine: Engine) -> None:
    inspector = inspect(engine)
    if "habit" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("habit")}
    with engine.begin() as connection:
        if "kind" not in columns:
            connection.execute(
                text("ALTER TABLE habit ADD COLUMN kind VARCHAR NOT NULL DEFAULT 'COUNT'")
            )
            # Enum columns store member names; a bool metric is a check habit, duration a timer.
            connection.execute(
                text(
                    "UPDATE habit SET kind = CASE "
                    "(SELECT upper(value_type) FROM metric WHERE metric.id = habit.metric_id) "
                    "WHEN 'BOOL' THEN 'CHECK' WHEN 'DURATION' THEN 'DURATION' ELSE 'COUNT' END"
                )
            )
        if "time_of_day" not in columns:
            connection.execute(
                text("ALTER TABLE habit ADD COLUMN time_of_day VARCHAR NOT NULL DEFAULT 'ANYTIME'")
            )
        if "archived_at" not in columns:
            connection.execute(text("ALTER TABLE habit ADD COLUMN archived_at DATETIME"))


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    event.listen(engine, "connect", _set_foreign_keys_pragma)


def _set_foreign_keys_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
