from atlas.cli.app import app
from tests.cli.conftest import invoke, seed_health


def test_log_records_a_numeric_value_and_marks_source_cli(runner):
    seed_health(runner)
    result = invoke(
        runner,
        ["log", "pushups", "40", "--on", "2026-08-10", "--note", "post-travel"],
    )

    assert "pushups" in result.output
    assert "40" in result.output
    assert "2026-08-10" in result.output
    assert "post-travel" in result.output
    assert "#" in result.output


def test_log_bool_metric_without_a_value_is_true(runner):
    seed_health(runner)
    result = invoke(runner, ["log", "meditated", "--on", "2026-08-13"])

    assert "meditated" in result.output
    assert "yes" in result.output


def test_log_resolves_a_unique_metric_prefix(runner):
    seed_health(runner)
    result = invoke(runner, ["log", "push", "40", "--on", "2026-08-10"])

    assert "pushups" in result.output
    assert result.exit_code == 0


def test_log_rejects_an_ambiguous_prefix(runner):
    seed_health(runner)
    invoke(
        runner,
        ["metric", "add", "protein", "--area", "health", "--type", "count", "--agg", "sum"],
    )
    result = runner.invoke(app, ["log", "p", "1"])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "ambiguous" in combined
    assert "protein" in combined
    assert "pushups" in combined


def test_unknown_metric_is_not_found(runner):
    seed_health(runner)
    result = runner.invoke(app, ["log", "missing", "1"])

    assert result.exit_code == 1
    assert "metric" in (result.output + (result.stderr or ""))
