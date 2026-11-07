def test_log_entry_accepts_a_metric_slug_and_marks_source_api(client, seed_health):
    response = client.post(
        "/entries",
        json={
            "metric": "pushups",
            "value": 40,
            "occurred_on": "2026-08-10",
            "note": "post-travel",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["metric"] == "pushups"
    assert body["value_num"] == 40.0
    assert body["occurred_on"] == "2026-08-10"
    assert body["note"] == "post-travel"
    assert body["source"] == "api"
    assert body["id"] is not None


def test_log_bool_metric_without_a_value_is_true(client, seed_health):
    response = client.post(
        "/entries",
        json={"metric": "meditated", "occurred_on": "2026-08-13"},
    )

    assert response.status_code == 201
    assert response.json()["value_bool"] is True
    assert response.json()["value_num"] is None


def test_amend_and_delete_entry(client, seed_health):
    created = client.post(
        "/entries",
        json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-13"},
    )
    entry_id = created.json()["id"]

    amended = client.patch(f"/entries/{entry_id}", json={"value": 40, "note": "fixed"})
    assert amended.status_code == 200
    assert amended.json()["value_num"] == 40.0
    assert amended.json()["note"] == "fixed"
    assert amended.json()["occurred_on"] == "2026-08-13"

    deleted = client.delete(f"/entries/{entry_id}")
    assert deleted.status_code == 204

    missing = client.delete(f"/entries/{entry_id}")
    assert missing.status_code == 404


def test_unknown_metric_is_not_found(client):
    response = client.post("/entries", json={"metric": "missing", "value": 1})

    assert response.status_code == 404
    assert "metric" in response.json()["detail"]


def test_list_entries_filters_and_orders_newest_first(client, seed_health):
    for body in (
        {"metric": "pushups", "value": 10, "occurred_on": "2026-08-10"},
        {"metric": "weight", "value": 78.4, "occurred_on": "2026-08-11"},
        {"metric": "pushups", "value": 20, "occurred_on": "2026-08-12"},
    ):
        assert client.post("/entries", json=body).status_code == 201

    everything = client.get("/entries")
    assert everything.status_code == 200
    assert [row["occurred_on"] for row in everything.json()] == [
        "2026-08-12",
        "2026-08-11",
        "2026-08-10",
    ]

    pushups = client.get(
        "/entries", params={"metric": "pushups", "start_on": "2026-08-11", "limit": 5}
    )
    assert [(row["metric"], row["value_num"]) for row in pushups.json()] == [("pushups", 20.0)]

    assert client.get("/entries", params={"metric": "missing"}).status_code == 404
    bad_range = client.get("/entries", params={"start_on": "2026-08-12", "end_on": "2026-08-10"})
    assert bad_range.status_code == 400
    assert client.get("/entries", params={"limit": 0}).status_code == 422


def test_list_entries_can_exclude_an_area(client, seed_health):
    client.post("/screen/categories", json={"slug": "entertainment", "judgment": "waste"})
    client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    session = client.post(
        "/screen/sessions",
        json={"app": "instagram", "minutes": 25, "occurred_on": "2026-08-13"},
    )
    assert session.status_code == 201, session.text
    client.post("/entries", json={"metric": "pushups", "value": 20, "occurred_on": "2026-08-13"})

    everything = client.get("/entries")
    assert {row["metric"] for row in everything.json()} == {"instagram", "pushups"}

    hidden = client.get("/entries", params={"exclude_area": "screen"})
    assert hidden.status_code == 200, hidden.text
    assert [row["metric"] for row in hidden.json()] == ["pushups"]


def test_excluding_an_unknown_area_excludes_nothing(client, seed_health):
    client.post("/entries", json={"metric": "pushups", "value": 20, "occurred_on": "2026-08-13"})

    response = client.get("/entries", params={"exclude_area": "screen"})

    assert response.status_code == 200
    assert [row["metric"] for row in response.json()] == ["pushups"]
