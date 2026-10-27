import json

from atlas.cli.app import app
from tests.cli.conftest import invoke, seed_health


def test_area_add(runner):
    created = invoke(runner, ["area", "add", "career"])
    assert "career" in created.output


def test_duplicate_area_slug_fails(runner):
    invoke(runner, ["area", "add", "health"])
    result = runner.invoke(app, ["area", "add", "health"])

    assert result.exit_code == 1
    assert "already exists" in (result.output + (result.stderr or ""))


def test_metric_add(runner):
    invoke(runner, ["area", "add", "health"])
    result = invoke(
        runner,
        ["metric", "add", "pushups", "--area", "health", "--type", "count", "--agg", "sum"],
    )
    assert "pushups" in result.output


def test_habit_add_defaults_slug_from_metric_and_period(runner):
    seed_health(runner)
    result = invoke(
        runner,
        ["habit", "add", "--metric", "pushups", "--period", "week", "--at-least", "3"],
    )
    assert "pushups-week" in result.output


def test_goal_add_infers_area_and_slug(runner):
    seed_health(runner)
    result = invoke(
        runner,
        [
            "goal",
            "add",
            "Bodyweight 75kg",
            "--metric",
            "weight",
            "--target",
            "75",
            "--at-most",
            "--by",
            "2026-12-01",
            "--start",
            "2026-01-01",
        ],
    )
    assert "bodyweight-75kg" in result.output


def test_goal_add_milestone_without_area(runner):
    seed_health(runner)
    result = invoke(
        runner,
        [
            "goal",
            "add",
            "Durable health",
            "--kind",
            "milestone",
            "--by",
            "2028-01-01",
            "--start",
            "2026-01-01",
        ],
    )
    assert "durable-health" in result.output


def test_goal_add_horizon_parent_and_cumulative(runner):
    seed_health(runner)
    invoke(
        runner,
        [
            "goal",
            "add",
            "Durable health",
            "--kind",
            "milestone",
            "--by",
            "2028-01-01",
            "--start",
            "2026-01-01",
            "--horizon",
            "long",
        ],
    )
    result = invoke(
        runner,
        [
            "goal",
            "add",
            "Ten thousand pushups",
            "--metric",
            "pushups",
            "--target",
            "10000",
            "--at-least",
            "--cumulative",
            "--by",
            "2026-12-01",
            "--start",
            "2026-01-01",
            "--horizon",
            "medium",
            "--parent",
            "durable-health",
        ],
    )
    assert "ten-thousand-pushups" in result.output
    payload = json.loads(invoke(runner, ["export"]).output)
    by_slug = {goal["slug"]: goal for goal in payload["goals"]}
    assert by_slug["durable-health"]["horizon"] == "long"
    assert by_slug["ten-thousand-pushups"]["horizon"] == "medium"
    assert by_slug["ten-thousand-pushups"]["parent"] == "durable-health"
    assert by_slug["ten-thousand-pushups"]["measure"] == "cumulative_since_start"


def test_habit_first_add_check_skip_and_archive(runner):
    created = invoke(
        runner,
        [
            "habit",
            "add",
            "--name",
            "Read",
            "--kind",
            "count",
            "--at-least",
            "20",
            "--unit",
            "pages",
            "--time",
            "evening",
            "--from",
            "2026-08-03",
        ],
    )
    assert "read" in created.output
    checked = invoke(runner, ["habit", "check", "read", "12", "--on", "2026-08-03"])
    assert "read: 12 2026-08-03" in checked.output
    skipped = invoke(
        runner, ["habit", "skip", "read", "--from", "2026-08-05", "--to", "2026-08-07"]
    )
    assert "2026-08-05 → 2026-08-07" in skipped.output
    invoke(runner, ["habit", "add", "--name", "No sugar", "--kind", "quit"])
    archived = invoke(runner, ["habit", "archive", "read"])
    assert "archived habit read" in archived.output
    exported = invoke(runner, ["export"])
    assert '"kind": "quit"' in exported.output
    assert '"time_of_day": "evening"' in exported.output
