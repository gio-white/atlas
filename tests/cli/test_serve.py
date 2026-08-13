import uvicorn
from typer.testing import CliRunner

from atlas.api.app import UVICORN_HOST, UVICORN_PORT
from atlas.cli.app import app


def test_serve_runs_uvicorn_on_localhost(monkeypatch):
    called: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        called["args"] = args
        called.update(kwargs)

    monkeypatch.setattr(uvicorn, "run", fake_run)
    result = CliRunner().invoke(app, ["serve"])

    assert result.exit_code == 0, result.output
    assert called["host"] == UVICORN_HOST == "127.0.0.1"
    assert called["port"] == UVICORN_PORT == 8000
