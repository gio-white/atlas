def _seed_daily_pushups(client):
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
    assert created.status_code == 201, created.text


def test_today_view_shows_due_habits_and_logged_entries(client, seed_health):
    _seed_daily_pushups(client)
    client.post("/entries", json={"metric": "pushups", "value": 40, "occurred_on": "2026-08-13"})
    client.post("/entries", json={"metric": "meditated", "occurred_on": "2026-08-13"})

    response = client.get("/views/today", params={"as_of": "2026-08-13"})
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2026-08-13"
    assert [habit["slug"] for habit in body["habits"]] == ["pushups-daily"]
    assert body["habits"][0]["satisfied"] is True
    assert {entry["metric_slug"] for entry in body["entries"]} == {"pushups", "meditated"}


def test_week_view_covers_the_iso_week(client, seed_health):
    _seed_daily_pushups(client)
    client.post("/entries", json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-10"})
    client.post("/entries", json={"metric": "pushups", "value": 20, "occurred_on": "2026-08-12"})

    response = client.get("/views/week", params={"as_of": "2026-08-13"})
    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-08-10"
    assert body["week_end"] == "2026-08-16"
    assert len(body["habits"]) == 1
    by_day = {cell["day"]: cell for cell in body["habits"][0]["days"]}
    assert by_day["2026-08-10"]["value"] == 10.0
    assert by_day["2026-08-10"]["satisfied"] is True
    assert by_day["2026-08-11"]["value"] is None
    assert by_day["2026-08-11"]["satisfied"] is False


def test_area_view_groups_metrics_habits_and_goals(client, seed_health):
    _seed_daily_pushups(client)
    client.post(
        "/goals",
        json={
            "slug": "bodyweight-75",
            "area": "health",
            "kind": "metric_target",
            "metric": "weight",
            "target_value": 75,
            "comparator": "at_most",
            "measure": "latest_value",
            "start_on": "2026-01-01",
            "due_on": "2026-12-31",
        },
    )
    client.post("/entries", json={"metric": "pushups", "value": 30, "occurred_on": "2026-08-13"})

    response = client.get("/views/areas/health", params={"as_of": "2026-08-13"})
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "health"
    assert {metric["slug"] for metric in body["metrics"]} == {"meditated", "pushups", "weight"}
    assert [habit["slug"] for habit in body["habits"]] == ["pushups-daily"]
    assert [goal["slug"] for goal in body["goals"]] == ["bodyweight-75"]


def test_home_week_view(client):
    client.post("/updates", json={"occurred_on": "2026-08-10"})
    client.post("/slips", json={"occurred_on": "2026-08-11"})
    response = client.get("/views/home", params={"as_of": "2026-08-14"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["week_start"] == "2026-08-10"
    assert body["updates"] == 1
    assert body["slips"] == 1
    assert body["series_updates"][0] == 1.0
    assert body["series_slips"][1] == 1.0
    assert body["focus_minutes"] == 0
    assert body["tasks_done"] == 0


def test_goals_board_view(client, seed_health):
    client.post(
        "/goals",
        json={
            "slug": "durable-health",
            "area": "health",
            "kind": "milestone",
            "start_on": "2026-01-01",
            "due_on": "2028-01-01",
        },
    )
    client.post(
        "/goals",
        json={
            "slug": "workout-week",
            "area": "health",
            "kind": "milestone",
            "start_on": "2026-08-10",
            "due_on": "2026-08-16",
            "horizon": "short",
        },
    )
    client.post(
        "/tasks",
        json={"title": "Pushups", "goal": "workout-week", "due_on": "2026-08-14"},
    )
    response = client.get("/views/goals", params={"as_of": "2026-08-14"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [goal["slug"] for goal in body["long"]["goals"]] == ["durable-health"]
    assert [goal["slug"] for goal in body["short"]["goals"]] == ["workout-week"]
    assert body["week"]["total"] == 1
    assert body["week"]["tasks"][0]["goal"] == "workout-week"
