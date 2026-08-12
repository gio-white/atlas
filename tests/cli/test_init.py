from sqlmodel import Session, create_engine
from typer.testing import CliRunner

from atlas.cli.app import app
from atlas.db import SchemaVersion


def test_init_creates_the_database_file(tmp_path, monkeypatch):
    db_path = tmp_path / "share" / "atlas.db"
    monkeypatch.setenv("ATLAS_DB", str(db_path))

    result = CliRunner().invoke(app, ["init"])

    assert result.exit_code == 0, result.output
    assert db_path.exists()
    assert str(db_path) in result.output

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1) is not None


def test_init_is_safe_to_run_twice(tmp_path, monkeypatch):
    db_path = tmp_path / "atlas.db"
    monkeypatch.setenv("ATLAS_DB", str(db_path))
    runner = CliRunner()

    first = runner.invoke(app, ["init"])
    second = runner.invoke(app, ["init"])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
