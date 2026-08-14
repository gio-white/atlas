import json

from atlas.db import CURRENT_SCHEMA_VERSION
from tests.cli.conftest import invoke, seed_health


def test_export_and_import_round_trip(runner, tmp_path):
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
    invoke(runner, ["log", "pushups", "40", "--on", "2026-08-10"])

    exported = invoke(runner, ["export"])
    payload = json.loads(exported.output)
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert [area["slug"] for area in payload["areas"]] == ["health"]
    assert {metric["slug"] for metric in payload["metrics"]} == {
        "meditated",
        "pushups",
        "weight",
    }
    assert payload["screen_categories"] == []
    assert payload["screen_apps"] == []
    assert payload["screen_budgets"] == []
    assert payload["entries"][0]["source"] == "cli"

    path = tmp_path / "atlas.json"
    path.write_text(exported.output)
    imported = invoke(runner, ["import", str(path), "--replace"])
    assert "imported" in imported.output or "replaced" in imported.output

    again = invoke(runner, ["export"])
    restored = json.loads(again.output)
    assert restored["areas"] == payload["areas"]
    assert restored["metrics"] == payload["metrics"]
    assert restored["habits"] == payload["habits"]
    assert len(restored["entries"]) == len(payload["entries"])
