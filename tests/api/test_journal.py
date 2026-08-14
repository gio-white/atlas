def test_post_and_get_journal(client):
    created = client.post(
        "/journal", json={"text": "shipped the dashboard", "occurred_on": "2026-08-14"}
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["metric"] == "journal"
    assert body["value_text"] == "shipped the dashboard"
    assert body["source"] == "api"

    day = client.get("/journal", params={"as_of": "2026-08-14"})
    assert day.status_code == 200, day.text
    payload = day.json()
    assert payload["text"] == "shipped the dashboard"
    assert payload["entry_id"] == body["id"]
    assert payload["as_of"] == "2026-08-14"


def test_get_journal_creates_catalog_when_empty(client):
    day = client.get("/journal", params={"as_of": "2026-08-14"})
    assert day.status_code == 200, day.text
    assert day.json()["text"] is None
    areas = client.get("/areas").json()
    assert "life" in {row["slug"] for row in areas}


def test_post_journal_rejects_blank_text(client):
    response = client.post("/journal", json={"text": "   "})
    assert response.status_code == 400
