def test_create_taxonomy_and_read_view(client):
    category = client.post(
        "/screen/categories",
        json={"slug": "entertainment", "judgment": "waste", "name": "Entertainment"},
    )
    assert category.status_code == 201, category.text
    assert category.json()["judgment"] == "waste"

    app = client.post(
        "/screen/apps",
        json={"slug": "instagram", "category": "entertainment", "name": "Instagram"},
    )
    assert app.status_code == 201, app.text
    assert app.json()["metric"] == "instagram"
    assert app.json()["category"] == "entertainment"

    budget = client.post(
        "/screen/budgets",
        json={
            "slug": "waste-cap",
            "name": "Waste cap",
            "target_kind": "judgment",
            "target_slug": "waste",
            "period": "day",
            "target_value": 90,
            "comparator": "at_most",
            "active_from": "2026-08-01",
        },
    )
    assert budget.status_code == 201, budget.text

    logged = client.post(
        "/entries",
        json={"metric": "instagram", "value": 30, "occurred_on": "2026-08-14"},
    )
    assert logged.status_code == 201, logged.text

    view = client.get("/screen/view", params={"as_of": "2026-08-14"})
    assert view.status_code == 200, view.text
    body = view.json()
    assert body["judgments"]["waste"] == 30.0
    assert body["judgments"]["total"] == 30.0
    assert body["budgets"][0]["current_value"] == 30.0
    assert body["budgets"][0]["satisfied"] is True
    assert body["sessions"][0]["app"] == "instagram"
    assert body["categories"][0]["apps"][0]["minutes"] == 30.0


def test_create_interval_session_and_device(client):
    client.post("/screen/categories", json={"slug": "entertainment", "judgment": "waste"})
    client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    device = client.post("/screen/devices", json={"slug": "iphone", "name": "iPhone"})
    assert device.status_code == 201, device.text

    created = client.post(
        "/screen/sessions",
        json={
            "app": "instagram",
            "device": "iphone",
            "started_at": "2026-08-14T20:00:00+00:00",
            "ended_at": "2026-08-14T20:30:00+00:00",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["minutes"] == 30.0
    assert body["device"] == "iphone"
    assert body["app"] == "instagram"

    listed = client.get("/screen/sessions", params={"occurred_on": "2026-08-14"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    removed = client.delete(f"/screen/sessions/{body['id']}")
    assert removed.status_code == 204
    assert client.get("/screen/sessions").json() == []


def test_patch_category_judgment_updates_view(client):
    client.post("/screen/categories", json={"slug": "entertainment", "judgment": "waste"})
    client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    client.post("/entries", json={"metric": "instagram", "value": 30, "occurred_on": "2026-08-14"})

    patched = client.patch("/screen/categories/entertainment", json={"judgment": "useful"})
    assert patched.status_code == 200
    assert patched.json()["judgment"] == "useful"

    view = client.get("/screen/view", params={"as_of": "2026-08-14"})
    assert view.json()["judgments"]["waste"] is None
    assert view.json()["judgments"]["useful"] == 30.0


def test_unknown_category_is_not_found(client):
    response = client.get("/screen/categories/missing")
    assert response.status_code == 404
    assert "screen_category" in response.json()["detail"]


def test_duplicate_app_slug_conflicts(client):
    client.post("/screen/categories", json={"slug": "entertainment", "judgment": "waste"})
    first = client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    assert first.status_code == 201
    again = client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    assert again.status_code == 409


def test_screen_dashboard_week(client):
    client.post("/screen/categories", json={"slug": "entertainment", "judgment": "waste"})
    client.post("/screen/apps", json={"slug": "instagram", "category": "entertainment"})
    logged = client.post(
        "/screen/sessions",
        json={"app": "instagram", "minutes": 30, "occurred_on": "2026-08-12"},
    )
    assert logged.status_code == 201, logged.text
    response = client.get(
        "/screen/dashboard",
        params={"period": "week", "as_of": "2026-08-14"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["period"] == "week"
    assert body["range_start"] == "2026-08-10"
    assert body["range_end"] == "2026-08-14"
    assert body["total"] == 30.0
    assert body["daily_average"] == 6.0
    assert len(body["hours"]) == 7
    assert len(body["trend"]) == 8
    assert body["apps"][0]["slug"] == "instagram"
    assert body["devices"][0]["slug"] == "unknown"
