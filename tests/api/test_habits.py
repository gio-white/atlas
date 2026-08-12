def test_create_habit_and_read_status(client, seed_health):
    created = client.post(
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
    assert created.status_code == 201
    assert created.json()["metric"] == "pushups"
    assert created.json()["period"] == "day"

    client.post("/entries", json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-11"})
    client.post("/entries", json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-12"})
    client.post("/entries", json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-13"})

    status = client.get("/habits/pushups-daily/status", params={"as_of": "2026-08-13"})
    assert status.status_code == 200
    body = status.json()
    assert body["current_streak"] == 3
    assert body["longest_streak"] == 3
    assert body["satisfied"] is True
    assert body["scheduled"] is True
    assert body["metric_slug"] == "pushups"


def test_list_habits_can_filter_by_metric(client, seed_health):
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

    listed = client.get("/habits", params={"metric": "pushups"})
    assert listed.status_code == 200
    assert [habit["slug"] for habit in listed.json()] == ["pushups-daily"]


def test_unknown_habit_status_is_not_found(client):
    response = client.get("/habits/missing/status")

    assert response.status_code == 404
    assert "habit" in response.json()["detail"]
