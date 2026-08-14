def test_post_and_get_updates(client):
    created = client.post("/updates", json={"occurred_on": "2026-08-13", "note": "here"})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["metric"] == "checkin"
    assert body["value_bool"] is True
    assert body["source"] == "api"
    assert body["note"] == "here"

    status = client.get("/updates", params={"as_of": "2026-08-13"})
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["checked_in"] is True
    assert payload["current_streak"] == 1
    assert payload["as_of"] == "2026-08-13"


def test_get_updates_creates_catalog_when_empty(client):
    status = client.get("/updates", params={"as_of": "2026-08-14"})
    assert status.status_code == 200, status.text
    assert status.json()["checked_in"] is False
    assert status.json()["current_streak"] == 0
    areas = client.get("/areas").json()
    assert "life" in {row["slug"] for row in areas}
