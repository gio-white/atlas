import pytest
from fastapi.testclient import TestClient

from atlas.api.app import create_app
from atlas.db import create_memory_engine, init_schema, make_session_factory


@pytest.fixture
def engine():
    engine = create_memory_engine()
    init_schema(engine)
    return engine


@pytest.fixture
def client(engine):
    application = create_app(session_factory=make_session_factory(engine))
    return TestClient(application)


@pytest.fixture
def seed_health(client):
    created = client.post("/areas", json={"slug": "health", "name": "Health"})
    assert created.status_code == 201, created.text
    for body in (
        {
            "slug": "pushups",
            "area": "health",
            "value_type": "count",
            "aggregation": "sum",
            "unit": "reps",
            "direction": "higher_is_better",
        },
        {
            "slug": "weight",
            "area": "health",
            "value_type": "quantity",
            "aggregation": "last",
            "unit": "kg",
            "direction": "lower_is_better",
        },
        {
            "slug": "meditated",
            "area": "health",
            "value_type": "bool",
            "aggregation": "sum",
            "direction": "higher_is_better",
        },
    ):
        response = client.post("/metrics", json=body)
        assert response.status_code == 201, response.text
