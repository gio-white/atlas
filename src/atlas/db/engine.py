from collections.abc import Callable
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from atlas.db.models import SchemaVersion

CURRENT_SCHEMA_VERSION = 3


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


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    event.listen(engine, "connect", _set_foreign_keys_pragma)


def _set_foreign_keys_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
