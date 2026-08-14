from datetime import date, timedelta

import pytest

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.domain import Period
from atlas.services import (
    ValidationError,
    export_all,
    screen_dashboard,
    seed_demo,
    today_view,
)


def test_seed_demo_loads_the_demo_dataset(session):
    as_of = date(2026, 8, 13)
    summary = seed_demo(session, as_of=as_of)

    assert summary.as_of == as_of
    assert summary.areas == 5
    assert summary.metrics == 17
    assert summary.habits == 6
    assert summary.goals == 7
    assert summary.milestones == 7
    assert summary.entries > 0
    assert summary.tasks == 3
    assert summary.screen_categories == 4
    assert summary.screen_apps == 6
    assert summary.screen_devices == 2
    assert summary.screen_sessions >= 28

    payload = export_all(session)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert {area["slug"] for area in payload["areas"]} == {
        "career",
        "finance",
        "health",
        "relationships",
        "screen",
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
    assert by_slug["durable-health"]["area"] is None
    assert by_slug["financial-freedom"]["area"] is None
    assert by_slug["bodyweight-75"]["area"] == "health"
    assert {task["title"] for task in payload["tasks"]} == {
        "Evening walk",
        "Meditate for 10 minutes",
        "Pushups - 3 sets",
    }
    occurred = {entry["occurred_on"] for entry in payload["entries"]}
    assert as_of.isoformat() in occurred
    assert (as_of - timedelta(days=27)).isoformat() in occurred
    assert all(entry["source"] == "import" for entry in payload["entries"])
    assert {row["slug"] for row in payload["screen_categories"]} == {
        "entertainment",
        "learning",
        "productivity",
        "social",
    }
    assert {row["slug"] for row in payload["screen_apps"]} == {
        "chatgpt",
        "instagram",
        "netflix",
        "vscode",
        "whatsapp",
        "youtube",
    }
    assert {row["slug"] for row in payload["screen_devices"]} == {"iphone", "macbook"}
    assert payload["screen_budgets"][0]["target_slug"] == "waste"
    assert len(payload["screen_sessions"]) >= 28
    interval = [row for row in payload["screen_sessions"] if row["started_at"]]
    duration_only = [row for row in payload["screen_sessions"] if row["started_at"] is None]
    assert len(interval) > len(duration_only)
    assert duration_only
    assert any(
        row["app"] == "youtube"
        and row["ended_at"] is not None
        and row["started_at"][:10] != row["ended_at"][:10]
        for row in interval
    )
    chain_days = {
        row["occurred_on"]
        for row in interval
        if row["app"] == "youtube" and row["started_at"][11:16] == "20:00"
    }
    instagram_follow = {
        row["occurred_on"]
        for row in interval
        if row["app"] == "instagram" and row["started_at"][11:16] == "20:40"
    }
    assert chain_days & instagram_follow


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


def test_seed_demo_fills_screen_dashboard(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    as_of = date(2026, 8, 13)
    seed_demo(session, as_of=as_of)
    dash = screen_dashboard(session, as_of=as_of, period=Period.WEEK)
    assert dash.total is not None and dash.total > 0
    assert any(sum(row) > 0 for row in dash.hours)
    assert any(item.kind.value == "sequence" for item in dash.insights)


def test_seed_demo_refuses_when_the_database_already_has_data(session):
    seed_demo(session, as_of=date(2026, 8, 13))
    with pytest.raises(ValidationError, match="already has data"):
        seed_demo(session, as_of=date(2026, 8, 13))


def test_seed_demo_replace_overwrites_without_duplicating_entries(session):
    as_of = date(2026, 8, 13)
    first = seed_demo(session, as_of=as_of)
    second = seed_demo(session, as_of=as_of, replace=True)
    assert second.entries == first.entries
    exported = export_all(session)
    assert len(exported["entries"]) == first.entries + len(exported["screen_sessions"])
