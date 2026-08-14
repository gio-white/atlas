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
