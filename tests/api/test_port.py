def test_export_and_import_round_trip(client, seed_health):
    client.post(
        "/habits",
        json={
            "slug": "pushups-daily",
            "metric": "pushups",
            "period": "day",
            "target_value": 1,
            "comparator": "at_least",
            "active_from": "2026-08-01",
        },
    )
    logged = client.post(
        "/entries",
        json={"metric": "pushups", "value": 40, "occurred_on": "2026-08-10"},
    )
    assert logged.status_code == 201

    exported = client.get("/export")
    assert exported.status_code == 200
    payload = exported.json()
    assert payload["schema_version"] == 1
    assert [area["slug"] for area in payload["areas"]] == ["health"]
    assert {metric["slug"] for metric in payload["metrics"]} == {
        "meditated",
        "pushups",
        "weight",
    }

    replaced = client.post("/import", params={"replace": True}, json=payload)
    assert replaced.status_code == 204

    again = client.get("/export")
    assert again.status_code == 200
    restored = again.json()
    assert restored["areas"] == payload["areas"]
    assert restored["metrics"] == payload["metrics"]
    assert restored["habits"] == payload["habits"]
    assert len(restored["entries"]) == len(payload["entries"])
