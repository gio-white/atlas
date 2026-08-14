from datetime import date

import pytest

from atlas.db import CURRENT_SCHEMA_VERSION, create_memory_engine, init_schema, make_session_factory
from atlas.domain import Comparator, GoalKind, Measure, Period, Source
from atlas.services import (
    MilestoneInput,
    ValidationError,
    create_goal,
    create_habit,
    export_all,
    import_all,
    list_areas,
    list_goals,
    list_habits,
    list_metrics,
    log_entry,
)
from tests.services.helpers import log_pushups, seed_health


def _populated(session):
    seed_health(session)
    create_habit(
        session,
        "pushups-daily",
        metric_slug="pushups",
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    create_goal(
        session,
        "bodyweight-75",
        area_slug="health",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
        milestones=[MilestoneInput("hit-78")],
    )
    log_pushups(session, date(2026, 8, 10), 40)
    log_entry(
        session,
        "weight",
        78.4,
        occurred_on=date(2026, 8, 10),
        note="post-travel",
        source=Source.CLI,
    )
    return export_all(session)


def test_export_round_trips_through_a_fresh_database(session):
    payload = _populated(session)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert [area["slug"] for area in payload["areas"]] == ["health"]
    assert {metric["slug"] for metric in payload["metrics"]} == {
        "meditated",
        "pushups",
        "weight",
    }

    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)

    assert restored["areas"] == payload["areas"]
    assert restored["metrics"] == payload["metrics"]
    assert restored["habits"] == payload["habits"]
    assert restored["goals"] == payload["goals"]
    assert restored["milestones"] == payload["milestones"]
    assert restored["screen_categories"] == payload["screen_categories"]
    assert restored["screen_apps"] == payload["screen_apps"]
    assert restored["screen_budgets"] == payload["screen_budgets"]
    assert restored["tasks"] == payload["tasks"]
    assert len(restored["entries"]) == len(payload["entries"])
    assert restored["entries"][0]["metric"] == "pushups"
    assert restored["entries"][0]["value_num"] == 40.0
    assert restored["entries"][1]["note"] == "post-travel"


def test_import_replace_clears_existing_rows(session):
    payload = _populated(session)
    log_pushups(session, date(2026, 8, 11), 5)

    import_all(session, payload, replace=True)

    assert [area.slug for area in list_areas(session)] == ["health"]
    assert [habit.slug for habit in list_habits(session)] == ["pushups-daily"]
    assert [goal.slug for goal in list_goals(session)] == ["bodyweight-75"]
    assert {metric.slug for metric in list_metrics(session)} == {
        "meditated",
        "pushups",
        "weight",
    }
    exported = export_all(session)
    assert len(exported["entries"]) == 2


def test_import_rejects_unknown_schema_version(session):
    with pytest.raises(ValidationError, match="schema_version"):
        import_all(session, {"schema_version": 99})


def test_import_accepts_schema_version_1(session):
    payload = _populated(session)
    payload["schema_version"] = 1
    payload.pop("screen_categories")
    payload.pop("screen_apps")
    payload.pop("screen_budgets")
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restored["screen_categories"] == []


def test_import_accepts_schema_version_2(session):
    payload = _populated(session)
    payload["schema_version"] = 2
    payload.pop("tasks", None)
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restored["tasks"] == []
