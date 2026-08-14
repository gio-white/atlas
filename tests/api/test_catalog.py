def test_get_patch_and_archive_area(client):
    client.post("/areas", json={"slug": "health", "name": "Health"})

    fetched = client.get("/areas/health")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Health"

    patched = client.patch("/areas/health", json={"name": "Wellness", "description": "body"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Wellness"
    assert patched.json()["description"] == "body"

    archived = client.post("/areas/health/archive")
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert client.get("/areas").json() == []


def test_get_patch_and_archive_metric(client, seed_health):
    fetched = client.get("/metrics/pushups")
    assert fetched.status_code == 200
    assert fetched.json()["area"] == "health"

    patched = client.patch("/metrics/pushups", json={"name": "Push-ups", "unit": "reps"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Push-ups"
    assert patched.json()["value_type"] == "count"

    archived = client.post("/metrics/pushups/archive")
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None


def test_get_and_patch_habit(client, seed_health):
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

    fetched = client.get("/habits/pushups-daily")
    assert fetched.status_code == 200
    assert fetched.json()["metric"] == "pushups"

    patched = client.patch(
        "/habits/pushups-daily",
        json={"target_value": 20, "weekdays": [1, 3, 5]},
    )
    assert patched.status_code == 200
    assert patched.json()["target_value"] == 20
    assert patched.json()["weekdays"] == [1, 3, 5]


def test_goal_detail_includes_milestones_and_toggle(client, seed_health):
    created = client.post(
        "/goals",
        json={
            "slug": "launch",
            "area": "health",
            "kind": "milestone",
            "start_on": "2026-01-01",
            "due_on": "2026-12-31",
            "milestones": [{"name": "Hit 78kg"}],
        },
    )
    assert created.status_code == 201

    detail = client.get("/goals/launch")
    assert detail.status_code == 200
    body = detail.json()
    assert body["slug"] == "launch"
    assert body["milestones"][0]["name"] == "Hit 78kg"
    assert body["milestones"][0]["done_at"] is None

    toggled = client.post("/goals/launch/milestones/Hit 78kg/toggle")
    assert toggled.status_code == 200
    assert toggled.json()["done_at"] is not None

    patched = client.patch("/goals/launch", json={"status": "paused", "name": "Launch later"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "paused"
    assert patched.json()["name"] == "Launch later"

    rejected = client.patch("/goals/launch", json={"status": "achieved"})
    assert rejected.status_code == 400


def test_unknown_catalog_slug_is_not_found(client):
    assert client.get("/areas/missing").status_code == 404
    assert client.get("/metrics/missing").status_code == 404
    assert client.get("/habits/missing").status_code == 404
    assert client.get("/goals/missing").status_code == 404
