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


def test_habits_calendar_week_covers_the_iso_week(client, seed_health):
    _seed_daily_pushups(client)
    client.post("/entries", json={"metric": "pushups", "value": 10, "occurred_on": "2026-08-10"})

    calendar = client.get(
        "/views/habits/calendar",
        params={"period": "week", "as_of": "2026-08-13"},
    )
    assert calendar.status_code == 200, calendar.text
    body = calendar.json()
    assert body["period"] == "week"
    assert body["range_start"] == "2026-08-10"
    assert body["range_end"] == "2026-08-16"
    assert [habit["slug"] for habit in body["habits"]] == ["pushups-daily"]
    assert body["habits"][0]["days"][0]["value"] == 10.0


def test_habits_calendar_month_spans_august(client, seed_health):
    _seed_daily_pushups(client)
    response = client.get(
        "/views/habits/calendar",
        params={"period": "month", "as_of": "2026-08-13"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["range_start"] == "2026-08-01"
    assert body["range_end"] == "2026-08-31"
    assert len(body["habits"][0]["days"]) == 31


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


def test_habits_board_view(client, seed_health):
    _seed_daily_pushups(client)
    created = client.post(
        "/habits",
        json={
            "slug": "pushups-weekly",
            "metric": "pushups",
            "period": "week",
            "target_value": 3,
            "comparator": "at_least",
            "active_from": "2026-08-01",
        },
    )
    assert created.status_code == 201, created.text
    client.post("/entries", json={"metric": "pushups", "value": 1, "occurred_on": "2026-08-13"})

    response = client.get("/views/habits", params={"as_of": "2026-08-13"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["as_of"] == "2026-08-13"
    assert [habit["slug"] for habit in body["day"]] == ["pushups-daily"]
    assert [habit["slug"] for habit in body["week"]] == ["pushups-weekly"]
    assert body["month"] == []
    assert body["scheduled"] == 2
    assert body["satisfied"] == 1
    assert body["day"][0]["current_streak"] == 1
