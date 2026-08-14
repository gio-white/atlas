from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, col, create_engine, select

from atlas.db.models import Entry, SchemaVersion, ScreenApp, ScreenSession
from atlas.domain import infer_horizon

CURRENT_SCHEMA_VERSION = 7


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
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        row = session.get(SchemaVersion, 1)
        previous = None if row is None else row.version
        if previous is not None and previous < CURRENT_SCHEMA_VERSION:
            _migrate_goal_hierarchy(engine, previous)
            if previous < 5:
                _backfill_screen_sessions(engine)
            if previous < 6:
                _make_goal_area_nullable(engine)
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


def _migrate_goal_hierarchy(engine: Engine, from_version: int) -> None:
    if from_version >= 4:
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "goal" in tables:
            goal_columns = {column["name"] for column in inspector.get_columns("goal")}
            if "horizon" not in goal_columns:
                connection.execute(
                    text("ALTER TABLE goal ADD COLUMN horizon VARCHAR NOT NULL DEFAULT 'LONG'")
                )
            if "parent_id" not in goal_columns:
                connection.execute(text("ALTER TABLE goal ADD COLUMN parent_id INTEGER"))
            if "description" not in goal_columns:
                connection.execute(text("ALTER TABLE goal ADD COLUMN description TEXT"))
        if "task" in tables:
            task_columns = {column["name"] for column in inspector.get_columns("task")}
            if "goal_id" not in task_columns:
                connection.execute(text("ALTER TABLE task ADD COLUMN goal_id INTEGER"))
    _normalize_horizon_enum_names(engine)
    _backfill_goal_horizons(engine)


def _normalize_horizon_enum_names(engine: Engine) -> None:
    inspector = inspect(engine)
    if "goal" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("goal")}
    if "horizon" not in columns:
        return
    with engine.begin() as connection:
        connection.execute(text("UPDATE goal SET horizon = 'LONG' WHERE lower(horizon) = 'long'"))
        connection.execute(
            text("UPDATE goal SET horizon = 'MEDIUM' WHERE lower(horizon) = 'medium'")
        )
        connection.execute(text("UPDATE goal SET horizon = 'SHORT' WHERE lower(horizon) = 'short'"))


def _backfill_goal_horizons(engine: Engine) -> None:
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT id, start_on, due_on FROM goal")).all()
        for row in rows:
            start_on = _as_date(row.start_on)
            due_on = _as_date(row.due_on)
            horizon = infer_horizon(start_on, due_on).value
            connection.execute(
                text("UPDATE goal SET horizon = :horizon WHERE id = :id"),
                {"horizon": horizon, "id": row.id},
            )


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


def _make_goal_area_nullable(engine: Engine) -> None:
    inspector = inspect(engine)
    if "goal" not in inspector.get_table_names():
        return
    columns = inspector.get_columns("goal")
    area_column = next((column for column in columns if column["name"] == "area_id"), None)
    if area_column is None or area_column["nullable"]:
        return
    names = [column["name"] for column in columns]
    quoted = ", ".join(names)
    with engine.connect() as connection:
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text("BEGIN"))
        try:
            connection.execute(
                text(
                    "CREATE TABLE goal__new ("
                    "id INTEGER PRIMARY KEY, "
                    "area_id INTEGER, "
                    "slug VARCHAR NOT NULL, "
                    "name VARCHAR NOT NULL, "
                    "kind VARCHAR NOT NULL, "
                    "metric_id INTEGER, "
                    "target_value FLOAT, "
                    "comparator VARCHAR, "
                    "baseline_value FLOAT, "
                    "measure VARCHAR, "
                    "start_on DATE NOT NULL, "
                    "due_on DATE NOT NULL, "
                    "horizon VARCHAR NOT NULL, "
                    "parent_id INTEGER, "
                    "description TEXT, "
                    "status VARCHAR NOT NULL, "
                    "achieved_at DATETIME)"
                )
            )
            connection.execute(text(f"INSERT INTO goal__new ({quoted}) SELECT {quoted} FROM goal"))
            connection.execute(text("DROP TABLE goal"))
            connection.execute(text("ALTER TABLE goal__new RENAME TO goal"))
            connection.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS ix_goal_slug ON goal (slug)")
            )
            connection.execute(text("COMMIT"))
        except Exception:
            connection.execute(text("ROLLBACK"))
            connection.execute(text("PRAGMA foreign_keys=ON"))
            raise
        connection.execute(text("PRAGMA foreign_keys=ON"))


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    event.listen(engine, "connect", _set_foreign_keys_pragma)


def _set_foreign_keys_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
