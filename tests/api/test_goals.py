def test_create_goal_and_read_progress(client, seed_health):
    created = client.post(
        "/goals",
        json={
            "slug": "bodyweight-75",
            "area": "health",
            "name": "Bodyweight 75kg",
            "kind": "metric_target",
            "metric": "weight",
            "target_value": 75,
            "comparator": "at_most",
            "measure": "latest_value",
            "start_on": "2026-01-01",
            "due_on": "2026-12-31",
        },
    )
    assert created.status_code == 201
    assert created.json()["metric"] == "weight"
    assert created.json()["area"] == "health"
    assert created.json()["status"] == "active"

    client.post("/entries", json={"metric": "weight", "value": 80, "occurred_on": "2026-01-01"})
    client.post("/entries", json={"metric": "weight", "value": 78, "occurred_on": "2026-06-01"})

    progress = client.get("/goals/bodyweight-75/progress", params={"as_of": "2026-07-01"})
    assert progress.status_code == 200
    body = progress.json()
    assert body["current"] == 78.0
    assert body["baseline"] == 80.0
    assert body["fraction"] == 0.4
    assert body["target_met"] is False
    assert body["pace"] == "behind"
    assert body["status"] == "active"


def test_meeting_the_target_marks_the_goal_achieved(client, seed_health):
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
    client.post("/entries", json={"metric": "weight", "value": 80, "occurred_on": "2026-01-01"})
    client.post("/entries", json={"metric": "weight", "value": 75, "occurred_on": "2026-08-01"})

    progress = client.get("/goals/bodyweight-75/progress", params={"as_of": "2026-08-01"})
    assert progress.status_code == 200
    assert progress.json()["target_met"] is True
    assert progress.json()["status"] == "achieved"
    assert progress.json()["pace"] == "achieved"


def test_list_goals_can_filter_by_area(client, seed_health):
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

    listed = client.get("/goals", params={"area": "health"})
    assert listed.status_code == 200
    assert [goal["slug"] for goal in listed.json()] == ["bodyweight-75"]


def test_create_goal_with_parent_and_horizon(client, seed_health):
    north = client.post(
        "/goals",
        json={
            "slug": "durable-health",
            "area": "health",
            "kind": "milestone",
            "start_on": "2026-01-01",
            "due_on": "2028-01-01",
            "horizon": "long",
            "description": "Stay strong.",
        },
    )
    assert north.status_code == 201, north.text
    assert north.json()["horizon"] == "long"
    child = client.post(
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
            "due_on": "2026-06-01",
            "parent": "durable-health",
        },
    )
    assert child.status_code == 201, child.text
    assert child.json()["parent"] == "durable-health"
    assert child.json()["horizon"] == "medium"
    listed = client.get("/goals", params={"horizon": "medium"})
    assert [goal["slug"] for goal in listed.json()] == ["bodyweight-75"]


def test_create_goal_without_area(client, seed_health):
    created = client.post(
        "/goals",
        json={
            "slug": "north",
            "kind": "milestone",
            "start_on": "2026-01-01",
            "due_on": "2028-01-01",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["area"] is None
    patched = client.patch("/goals/north", json={"area": "health"})
    assert patched.status_code == 200
    assert patched.json()["area"] == "health"
    cleared = client.patch("/goals/north", json={"area": None})
    assert cleared.status_code == 200
    assert cleared.json()["area"] is None
