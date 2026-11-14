from datetime import UTC, date, datetime, timedelta

import pytest

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.domain import ChapterState, Period, QuestStatus
from atlas.services import (
    ValidationError,
    export_all,
    habit_statuses,
    list_entries,
    screen_dashboard,
    seed_demo,
    sleep_view,
)
from atlas.services.quest_views import (
    goal_view,
    inbox_view,
    main_quests_view,
    side_quests_view,
    today_view,
)


def test_seed_demo_loads_the_demo_dataset(session):
    as_of = date(2026, 8, 13)
    summary = seed_demo(session, as_of=as_of)

    assert summary.as_of == as_of
    assert summary.metrics == 18
    assert summary.habits == 7
    assert summary.entries > 0
    assert summary.screen_categories == 4
    assert summary.screen_apps == 6
    assert summary.screen_devices == 2
    assert summary.screen_sessions >= 28
    assert summary.library_topics == 4
    assert summary.library_titles == 9

    payload = export_all(session)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert "areas" not in payload
    origins = {metric["slug"]: metric["origin"] for metric in payload["metrics"]}
    assert origins["pushups"] == "manual"
    assert origins["no-doomscrolling"] == "habit"
    assert origins["journal"] == "journal"
    assert sorted(origins.values()).count("screen") == summary.screen_apps
    assert {habit["slug"] for habit in payload["habits"]} == {
        "coffee-daily",
        "deep-work-weekdays",
        "family-monthly",
        "meditated-daily",
        "no-doomscrolling",
        "pushups-daily",
        "runs-weekly",
    }
    habits = {habit["slug"]: habit for habit in payload["habits"]}
    assert habits["no-doomscrolling"]["kind"] == "quit"
    assert habits["meditated-daily"]["breaks"][0]["note"] == "Travel day"
    assert habits["pushups-daily"]["time_of_day"] == "morning"
    assert habits["meditated-daily"]["name"] == "Meditate"
    assert habits["deep-work-weekdays"]["name"] == "Deep work on weekdays"
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
    assert {row["slug"] for row in payload["library_topics"]} == {
        "finance",
        "math",
        "physics",
        "programming",
    }
    assert len(payload["library_titles"]) == 9
    assert {row["kind"] for row in payload["library_titles"]} >= {
        "book",
        "film",
        "series",
        "anime",
        "video",
        "podcast",
        "music",
    }
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
    slugs = {status.slug for status in habit_statuses(session, as_of=as_of) if status.scheduled}
    assert "pushups-daily" in slugs
    assert "meditated-daily" in slugs
    assert "coffee-daily" in slugs
    assert list_entries(session, start_on=as_of, end_on=as_of)


def test_seed_demo_fills_screen_dashboard(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    as_of = date(2026, 8, 13)
    seed_demo(session, as_of=as_of)
    dash = screen_dashboard(session, as_of=as_of, period=Period.WEEK)
    assert dash.total is not None and dash.total > 0
    assert any(sum(row) > 0 for row in dash.hours)
    assert any(item.kind.value == "sequence" for item in dash.insights)


def test_seed_demo_fills_sleep_view(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    as_of = date(2026, 8, 13)
    summary = seed_demo(session, as_of=as_of)
    view = sleep_view(session, as_of=as_of)
    assert summary.sleep_sessions > 20
    assert view.nights_logged >= 6
    assert view.night is not None
    assert view.night.stages.deep > 0
    assert view.night.stages.rem > 0


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


def test_seed_demo_covers_every_quest_structure(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    as_of = date(2026, 8, 13)
    summary = seed_demo(session, as_of=as_of)
    assert (summary.ambitions, summary.goals, summary.side_quests) == (2, 4, 2)
    assert summary.time_blocks == 8

    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    main = main_quests_view(session, now=now)
    engineer, calm = main.ambitions
    assert len(engineer.goals) == 2 and engineer.tasks
    assert calm.goals == [] and calm.tasks == [] and calm.ambition.progress is None
    independent = {goal.title: goal for goal in main.independent_goals}
    assert set(independent) == {"Run a half marathon", "Furnish the new flat"}
    flat = independent["Furnish the new flat"]
    assert flat.status is QuestStatus.COMPLETED and flat.completed_with_open_items

    tree = goal_view(session, engineer.goals[0].id, now=now)
    rust = tree.milestones[0]
    assert rust.chapters and rust.tasks
    states = {item.chapter.title: item.chapter.state for item in rust.chapters}
    assert states == {
        "Rust fundamentals": ChapterState.IN_PROGRESS,
        "Async Rust": ChapterState.EMPTY,
    }
    assert tree.tasks

    sides = side_quests_view(session, now=now)
    taxes = next(item for item in sides.side_quests if item.title == "Tax declaration")
    assert taxes.chapter_count == 1 and taxes.task_count == 1
    assert {task.title for task in sides.standalone_tasks} == {
        "Renew passport",
        "Fix the bike light",
    }
    assert inbox_view(session, now=now).count == 3

    today = today_view(session, as_of=as_of, now=now)
    assert len(today.blocks) == 3
    assert [item.task.title for item in today.unconfirmed] == [
        "Read Designing Data-Intensive Applications"
    ]
    assert [task.title for task in today.due_today] == ["Renew passport"]
    assert today.up_next
