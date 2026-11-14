from datetime import UTC, date, datetime

import pytest

from atlas.db import CURRENT_SCHEMA_VERSION, create_memory_engine, init_schema, make_session_factory
from atlas.domain import (
    Comparator,
    Period,
    ScreenJudgment,
    SleepStage,
    SleepStageSpan,
    Source,
)
from atlas.services import (
    ValidationError,
    create_habit,
    create_screen_app,
    create_screen_category,
    create_screen_device,
    export_all,
    import_all,
    list_habits,
    list_metrics,
    log_entry,
    log_screen_session,
    log_sleep_session,
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
    assert "areas" not in payload
    assert {metric["origin"] for metric in payload["metrics"]} == {"manual"}
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

    assert restored["metrics"] == payload["metrics"]
    assert restored["habits"] == payload["habits"]
    assert restored["screen_categories"] == payload["screen_categories"]
    assert restored["screen_apps"] == payload["screen_apps"]
    assert restored["screen_budgets"] == payload["screen_budgets"]
    assert len(restored["entries"]) == len(payload["entries"])
    assert restored["entries"][0]["metric"] == "pushups"
    assert restored["entries"][0]["value_num"] == 40.0
    assert restored["entries"][1]["note"] == "post-travel"


def test_import_replace_clears_existing_rows(session):
    payload = _populated(session)
    log_pushups(session, date(2026, 8, 11), 5)

    import_all(session, payload, replace=True)

    assert [habit.slug for habit in list_habits(session)] == ["pushups-daily"]
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
    payload.pop("screen_devices", None)
    payload.pop("screen_sessions", None)
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
    payload.pop("screen_devices", None)
    payload.pop("screen_sessions", None)
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION


def test_import_accepts_schema_version_4(session):
    payload = _populated(session)
    payload["schema_version"] = 4
    payload.pop("screen_devices", None)
    payload.pop("screen_sessions", None)
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restored["screen_devices"] == []
    assert restored["screen_sessions"] == []


def test_import_accepts_schema_version_5(session):
    payload = _populated(session)
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "instagram", category_slug="entertainment")
    create_screen_device(session, "iphone")
    log_screen_session(
        session,
        "instagram",
        minutes=30,
        occurred_on=date(2026, 8, 14),
        device_slug="iphone",
    )
    payload = export_all(session)
    payload["schema_version"] = 5
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION
    assert [row["slug"] for row in restored["screen_devices"]] == ["iphone"]
    assert restored["screen_sessions"][0]["app"] == "instagram"
    assert restored["screen_sessions"][0]["minutes"] == 30.0


def test_import_accepts_schema_version_6(session):
    payload = _populated(session)
    payload["schema_version"] = 6
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION


def test_import_accepts_schema_version_7(session):
    payload = _populated(session)
    payload["schema_version"] = 7
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
    assert restored["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restored["library_topics"] == payload.get("library_topics", [])


def test_export_round_trips_sleep_sessions(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    log_sleep_session(
        session,
        started_at=datetime(2026, 8, 12, 23, 0, tzinfo=UTC),
        ended_at=datetime(2026, 8, 13, 7, 0, tzinfo=UTC),
        stages=[
            SleepStageSpan(
                SleepStage.DEEP,
                datetime(2026, 8, 13, 1, 0, tzinfo=UTC),
                datetime(2026, 8, 13, 2, 0, tzinfo=UTC),
            )
        ],
    )
    payload = export_all(session)
    assert payload["sleep_sessions"][0]["occurred_on"] == "2026-08-13"
    assert payload["sleep_sessions"][0]["stages"][0]["stage"] == "deep"

    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        assert export_all(other)["sleep_sessions"] == payload["sleep_sessions"]
        import_all(other, payload, replace=True)
        assert len(export_all(other)["sleep_sessions"]) == 1


V10_LEGACY_SECTIONS = {
    "goals": [
        {
            "slug": "bodyweight-75",
            "area": "health",
            "name": "Bodyweight 75kg",
            "kind": "metric_target",
            "start_on": "2026-01-01",
            "due_on": "2026-12-01",
            "horizon": "medium",
            "status": "active",
        }
    ],
    "milestones": [{"goal": "bodyweight-75", "name": "Hit 78kg", "due_on": None}],
    "tasks": [{"title": "Family time", "bucket": "today", "priority": "normal"}],
}


def test_import_of_a_v10_export_ignores_old_goals_and_tasks(session):
    payload = _populated(session)
    payload["schema_version"] = 10
    for section in ("ambitions", "side_quests", "chapters", "time_blocks"):
        payload.pop(section)
    payload.update(V10_LEGACY_SECTIONS)
    payload["habits"][0]["goal"] = "bodyweight-75"
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        summary = import_all(other, payload)
        restored = export_all(other)

    assert summary.ignored_sections == ("goals", "milestones", "tasks")
    assert summary.notes == [
        "Skipped goals, milestones, tasks from this version 10 export: "
        "quests replaced the old goals and tasks."
    ]
    assert [habit["slug"] for habit in restored["habits"]] == ["pushups-daily"]
    assert "goal" not in restored["habits"][0]
    for section in ("ambitions", "goals", "milestones", "tasks", "time_blocks"):
        assert restored[section] == []


def test_import_of_a_v10_export_without_old_sections_reports_nothing(session):
    payload = _populated(session)
    payload["schema_version"] = 10
    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        assert import_all(other, payload).ignored_sections == ()


def _quest_payload() -> dict:
    stamp = "2026-11-08T09:00:00+00:00"
    return {
        "ambitions": [{"id": 7, "title": "Grow", "position": 0, "status": "active"}],
        "goals": [{"id": 3, "ambition_id": 7, "title": "Ship", "status": "active"}],
        "milestones": [{"id": 4, "goal_id": 3, "title": "Beta", "status": "active"}],
        "side_quests": [{"id": 9, "title": "Taxes", "status": "active"}],
        "chapters": [
            {"id": 5, "milestone_id": 4, "title": "Build"},
            {"id": 6, "side_quest_id": 9, "title": "Papers"},
        ],
        "tasks": [
            {"id": 11, "title": "Inbox idea", "status": "todo", "priority": "normal"},
            {
                "id": 12,
                "title": "Write code",
                "status": "completed",
                "priority": "high",
                "chapter_id": 5,
                "organized_at": stamp,
                "started_at": stamp,
                "completed_at": stamp,
                "estimate_minutes": 90,
            },
        ],
        "time_blocks": [
            {
                "id": 21,
                "task_id": 12,
                "start_at": "2026-11-08T10:00:00+00:00",
                "end_at": "2026-11-08T11:00:00+00:00",
                "status": "completed",
                "provider": "internal",
            }
        ],
    }


def test_quests_round_trip_with_remapped_ids(session):
    payload = {"schema_version": CURRENT_SCHEMA_VERSION, **_quest_payload()}
    import_all(session, payload)
    first = export_all(session)
    assert first["chapters"][0]["milestone_id"] == first["milestones"][0]["id"]
    assert first["tasks"][1]["chapter_id"] == first["chapters"][0]["id"]
    assert first["time_blocks"][0]["task_id"] == first["tasks"][1]["id"]
    assert first["tasks"][1]["estimate_minutes"] == 90

    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, first)
        import_all(other, first, replace=True)
        restored = export_all(other)
    for section in ("ambitions", "goals", "milestones", "side_quests", "chapters", "tasks"):
        assert len(restored[section]) == len(first[section])
    assert restored["time_blocks"][0]["status"] == "completed"
    assert restored["time_blocks"][0]["task_id"] == restored["tasks"][1]["id"]


def test_quest_import_rejects_a_dangling_reference(session):
    payload = {"schema_version": CURRENT_SCHEMA_VERSION, **_quest_payload()}
    payload["milestones"][0]["goal_id"] = 99
    with pytest.raises(ValidationError, match="goal_id"):
        import_all(session, payload)


def _v11_export_with_areas() -> dict:
    """The shape exports had before schema 12: an `areas` section, and each metric names its
    area instead of carrying an origin."""

    def metric(slug: str, area: str, value_type: str = "count", **extra) -> dict:
        return {
            "slug": slug,
            "area": area,
            "name": slug.title(),
            "value_type": value_type,
            "unit": None,
            "aggregation": "last" if value_type == "text" else "sum",
            "direction": "neutral",
            "archived_at": None,
            **extra,
        }

    return {
        "schema_version": 11,
        "areas": [
            {"slug": "health", "name": "Health", "description": None, "archived_at": None},
            {"slug": "habits", "name": "Habits", "description": None, "archived_at": None},
            {"slug": "screen", "name": "Screen", "description": None, "archived_at": None},
            {"slug": "life", "name": "Life", "description": None, "archived_at": None},
            {
                "slug": "old",
                "name": "Old",
                "description": None,
                "archived_at": "2026-05-01T00:00:00+00:00",
            },
        ],
        "metrics": [
            metric("pushups", "health"),
            metric("meditate", "habits", "bool"),
            metric("instagram", "screen", "duration"),
            metric("journal", "life", "text"),
            metric("retired", "old"),
            metric("retired-earlier", "old", archived_at="2026-01-01T00:00:00+00:00"),
        ],
    }


def test_import_of_a_v11_export_turns_areas_into_metric_origins(session):
    summary = import_all(session, _v11_export_with_areas())

    origins = {
        metric.slug: str(metric.origin) for metric in list_metrics(session, include_archived=True)
    }
    assert origins == {
        "pushups": "manual",
        "meditate": "habit",
        "instagram": "screen",
        "journal": "journal",
        "retired": "manual",
        "retired-earlier": "manual",
    }
    assert summary.ignored_sections == ("areas",)
    assert summary.notes == [
        "Skipped areas from this version 11 export: Atlas no longer groups metrics into areas. "
        "Every metric and habit was kept."
    ]
    assert "areas" not in export_all(session)


def test_import_of_a_v11_export_keeps_metrics_of_an_archived_area_archived(session):
    import_all(session, _v11_export_with_areas())

    by_slug = {metric.slug: metric for metric in list_metrics(session, include_archived=True)}
    assert by_slug["pushups"].archived_at is None
    assert by_slug["retired"].archived_at is not None
    assert by_slug["retired-earlier"].archived_at.year == 2026
    assert by_slug["retired-earlier"].archived_at.month == 1
    assert {metric.slug for metric in list_metrics(session)} == {
        "pushups",
        "meditate",
        "instagram",
        "journal",
    }


def test_import_marks_a_screen_apps_metric_as_screen_even_if_the_export_says_manual(session):
    payload = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "metrics": [
            {
                "slug": "instagram",
                "origin": "manual",
                "name": "Instagram",
                "value_type": "duration",
                "unit": "min",
                "aggregation": "sum",
                "direction": "lower_is_better",
                "archived_at": None,
            }
        ],
        "screen_categories": [
            {"slug": "social", "name": "Social", "judgment": "waste", "archived_at": None}
        ],
        "screen_apps": [
            {
                "slug": "instagram",
                "name": "Instagram",
                "category": "social",
                "metric": "instagram",
                "archived_at": None,
            }
        ],
    }

    import_all(session, payload)

    assert [str(metric.origin) for metric in list_metrics(session)] == ["screen"]


def test_import_of_an_export_before_schema_13_reads_the_entertainment_sections(session):
    payload = {
        "schema_version": 12,
        "metrics": [],
        "entries": [],
        "habits": [],
        "entertainment_topics": [{"slug": "jazz", "name": "Jazz"}],
        "entertainment_titles": [
            {"slug": "kind-of-blue", "name": "Kind of Blue", "kind": "music", "topics": ["jazz"]}
        ],
    }

    import_all(session, payload)

    restored = export_all(session)
    assert [topic["slug"] for topic in restored["library_topics"]] == ["jazz"]
    assert [(title["slug"], title["topics"]) for title in restored["library_titles"]] == [
        ("kind-of-blue", ["jazz"])
    ]
