from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from atlas.db.models import SchemaVersion
from atlas.domain import infer_horizon

CURRENT_SCHEMA_VERSION = 4


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
