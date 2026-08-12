import pytest

from atlas.db import create_memory_engine, init_schema, make_session_factory


@pytest.fixture
def session():
    engine = create_memory_engine()
    init_schema(engine)
    factory = make_session_factory(engine)
    with factory() as db_session:
        yield db_session
