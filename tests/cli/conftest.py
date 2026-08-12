from pathlib import Path

import pytest
from typer.testing import CliRunner

from atlas.cli.app import app


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "atlas.db"
    monkeypatch.setenv("ATLAS_DB", str(path))
    return path


@pytest.fixture
def runner(db_path) -> CliRunner:
    cli = CliRunner()
    result = cli.invoke(app, ["init"])
    assert result.exit_code == 0, result.output
    return cli


def invoke(runner: CliRunner, args: list[str]):
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output + (result.stderr or "")
    return result


def seed_health(runner: CliRunner) -> None:
    invoke(runner, ["area", "add", "health", "--name", "Health"])
    invoke(
        runner,
        [
            "metric",
            "add",
            "pushups",
            "--area",
            "health",
            "--type",
            "count",
            "--agg",
            "sum",
            "--unit",
            "reps",
            "--direction",
            "higher_is_better",
        ],
    )
    invoke(
        runner,
        [
            "metric",
            "add",
            "weight",
            "--area",
            "health",
            "--type",
            "quantity",
            "--agg",
            "last",
            "--unit",
            "kg",
            "--direction",
            "lower_is_better",
        ],
    )
    invoke(
        runner,
        [
            "metric",
            "add",
            "meditated",
            "--area",
            "health",
            "--type",
            "bool",
            "--agg",
            "sum",
        ],
    )
