from atlas.cli.app import app
from tests.cli.conftest import invoke, seed_health


def test_area_add_and_show(runner):
    seed_health(runner)
    invoke(
        runner,
        [
            "habit",
            "add",
            "pushups-daily",
            "--metric",
            "pushups",
            "--period",
            "day",
            "--at-least",
            "1",
            "--from",
            "2026-08-01",
        ],
    )
    invoke(runner, ["log", "pushups", "30", "--on", "2026-08-13"])

    created = invoke(runner, ["area", "add", "career"])
    assert "career" in created.output

    shown = invoke(runner, ["area", "health", "--on", "2026-08-13"])
    assert "health" in shown.output
    assert "pushups" in shown.output
    assert "pushups-daily" in shown.output


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
