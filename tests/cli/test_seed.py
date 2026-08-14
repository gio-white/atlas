from atlas.cli.app import app
from tests.cli.conftest import invoke


def test_seed_loads_demo(runner):
    result = invoke(runner, ["seed"])
    assert "seeded demo as of" in result.output
    assert "areas" in result.output
    assert "entries" in result.output

    exported = invoke(runner, ["export"])
    assert "meditated-daily" in exported.output


def test_seed_refuses_when_the_database_already_has_data(runner):
    invoke(runner, ["seed"])
    result = runner.invoke(app, ["seed"])
    assert result.exit_code == 1
    assert "already has data" in (result.output + (result.stderr or ""))


def test_seed_replace_overwrites(runner):
    invoke(runner, ["seed"])
    result = invoke(runner, ["seed", "--replace"])
    assert "seeded demo as of" in result.output
