from tests.cli.conftest import invoke, seed_health


def _seed_daily_pushups(runner):
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


def test_today_shows_due_habits_and_logged_entries(runner):
    _seed_daily_pushups(runner)
    invoke(runner, ["log", "pushups", "40", "--on", "2026-08-13"])
    invoke(runner, ["log", "meditated", "--on", "2026-08-13"])

    result = invoke(runner, ["today", "--on", "2026-08-13"])
    assert "2026-08-13" in result.output
    assert "pushups-daily" in result.output
    assert "pushups" in result.output
    assert "meditated" in result.output
    assert "Daily" in result.output
    assert "Logged" in result.output
    assert "Goals" in result.output


def test_today_splits_daily_and_period_habits(runner):
    _seed_daily_pushups(runner)
    invoke(
        runner,
        [
            "habit",
            "add",
            "pushups-week",
            "--metric",
            "pushups",
            "--period",
            "week",
            "--at-least",
            "3",
            "--from",
            "2026-08-01",
        ],
    )

    result = invoke(runner, ["today", "--on", "2026-08-13"])
    assert "Daily" in result.output
    assert "This period" in result.output
    assert "pushups-daily" in result.output
    assert "pushups-week" in result.output


def test_week_covers_the_iso_week(runner):
    _seed_daily_pushups(runner)
    invoke(runner, ["log", "pushups", "10", "--on", "2026-08-10"])
    invoke(runner, ["log", "pushups", "20", "--on", "2026-08-12"])

    result = invoke(runner, ["week", "--on", "2026-08-13"])
    assert "2026-08-10" in result.output
    assert "2026-08-16" in result.output
    assert "Habits" in result.output
    assert "pushups-daily" in result.output
    assert "10" in result.output
    assert "20" in result.output


def test_habit_show_prints_streak_and_adherence(runner):
    _seed_daily_pushups(runner)
    invoke(runner, ["log", "pushups", "10", "--on", "2026-08-11"])
    invoke(runner, ["log", "pushups", "10", "--on", "2026-08-12"])
    invoke(runner, ["log", "pushups", "10", "--on", "2026-08-13"])

    result = invoke(runner, ["habit", "pushups-daily", "--on", "2026-08-13"])
    assert "pushups-daily" in result.output
    assert "Status" in result.output
    assert "streak" in result.output
    assert "3" in result.output


def test_goals_prints_progress_and_pace(runner):
    seed_health(runner)
    invoke(
        runner,
        [
            "goal",
            "add",
            "Bodyweight 75kg",
            "--slug",
            "bodyweight-75",
            "--metric",
            "weight",
            "--target",
            "75",
            "--at-most",
            "--start",
            "2026-01-01",
            "--by",
            "2026-12-31",
        ],
    )
    invoke(runner, ["log", "weight", "80", "--on", "2026-01-01"])
    invoke(runner, ["log", "weight", "78", "--on", "2026-06-01"])

    result = invoke(runner, ["goals", "--on", "2026-07-01"])
    assert "Goals" in result.output
    assert "bodyweight-75" in result.output
    assert "behind" in result.output
    assert "40%" in result.output
