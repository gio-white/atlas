from datetime import date, timedelta

import pytest

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.services import (
    ValidationError,
    export_all,
    seed_demo,
    today_view,
)


def test_seed_demo_loads_the_demo_dataset(session):
    as_of = date(2026, 8, 13)
    summary = seed_demo(session, as_of=as_of)

    assert summary.as_of == as_of
    assert summary.areas == 4
    assert summary.metrics == 11
    assert summary.habits == 6
    assert summary.goals == 7
    assert summary.milestones == 7
    assert summary.entries > 0

    payload = export_all(session)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert {area["slug"] for area in payload["areas"]} == {
        "career",
        "finance",
        "health",
        "relationships",
    }
    assert {habit["slug"] for habit in payload["habits"]} == {
        "coffee-daily",
        "deep-work-weekdays",
        "family-monthly",
        "meditated-daily",
        "pushups-daily",
        "runs-weekly",
    }
    assert {goal["slug"] for goal in payload["goals"]} == {
        "bodyweight-75",
        "durable-health",
        "emergency-fund",
        "financial-freedom",
        "read-12-books",
        "ship-side-project",
        "workout-this-week",
    }
    by_slug = {goal["slug"]: goal for goal in payload["goals"]}
    assert by_slug["bodyweight-75"]["parent"] == "durable-health"
    assert by_slug["bodyweight-75"]["horizon"] == "medium"
    assert {task["title"] for task in payload["tasks"]} == {
        "Evening walk",
        "Meditate for 10 minutes",
        "Pushups - 3 sets",
    }
    occurred = {entry["occurred_on"] for entry in payload["entries"]}
    assert as_of.isoformat() in occurred
    assert (as_of - timedelta(days=27)).isoformat() in occurred
    assert all(entry["source"] == "import" for entry in payload["entries"])


def test_seed_demo_makes_today_reviewable(session):
    as_of = date(2026, 8, 13)
    seed_demo(session, as_of=as_of)
    view = today_view(session, as_of=as_of)
    slugs = {habit.slug for habit in view.habits}
    assert "pushups-daily" in slugs
    assert "meditated-daily" in slugs
    assert "coffee-daily" in slugs
    assert view.entries
    assert view.goals


def test_seed_demo_refuses_when_the_database_already_has_data(session):
    seed_demo(session, as_of=date(2026, 8, 13))
    with pytest.raises(ValidationError, match="already has data"):
        seed_demo(session, as_of=date(2026, 8, 13))


def test_seed_demo_replace_overwrites_without_duplicating_entries(session):
    as_of = date(2026, 8, 13)
    first = seed_demo(session, as_of=as_of)
    second = seed_demo(session, as_of=as_of, replace=True)
    assert second.entries == first.entries
    assert len(export_all(session)["entries"]) == first.entries
