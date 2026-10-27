import json

from atlas.cli.app import app
from atlas.db import CURRENT_SCHEMA_VERSION
from tests.cli.conftest import invoke


def test_export_and_import_round_trip(runner, tmp_path):
    invoke(runner, ["seed", "--on", "2026-08-14"])

    exported = invoke(runner, ["export"])
    payload = json.loads(exported.output)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert payload["areas"]
    assert payload["entries"]

    path = tmp_path / "atlas.json"
    path.write_text(exported.output)
    imported = invoke(runner, ["import", str(path), "--replace"])
    assert "replaced and imported" in imported.output

    restored = json.loads(invoke(runner, ["export"]).output)
    assert restored["areas"] == payload["areas"]
    assert restored["metrics"] == payload["metrics"]
    assert restored["habits"] == payload["habits"]
    assert len(restored["entries"]) == len(payload["entries"])


def test_import_rejects_invalid_json(runner, tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json")
    result = runner.invoke(app, ["import", str(path)])
    assert result.exit_code == 1
    assert "invalid JSON" in (result.output + (result.stderr or ""))
