def test_list_metrics_returns_each_metric_with_its_origin(client, seed_health):
    listed = client.get("/metrics")
    assert listed.status_code == 200
    slugs = {metric["slug"] for metric in listed.json()}
    assert slugs == {"meditated", "pushups", "weight"}
    pushups = next(metric for metric in listed.json() if metric["slug"] == "pushups")
    assert pushups["origin"] == "manual"
    assert pushups["value_type"] == "count"
    assert pushups["aggregation"] == "sum"
    assert "area" not in pushups


def test_create_metric_from_a_name_alone(client):
    response = client.post(
        "/metrics",
        json={"name": "Glasses of water", "value_type": "count", "aggregation": "sum"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["slug"] == "glasses-of-water"
    assert body["name"] == "Glasses of water"
    assert body["origin"] == "manual"

    again = client.post(
        "/metrics",
        json={"name": "Glasses of water", "value_type": "count", "aggregation": "sum"},
    )
    assert again.status_code == 409

    nameless = client.post("/metrics", json={"value_type": "count", "aggregation": "sum"})
    assert nameless.status_code == 400


def test_create_metric_no_longer_takes_an_area_or_an_origin(client):
    for extra in ({"area": "health"}, {"origin": "screen"}):
        response = client.post(
            "/metrics",
            json={"slug": "pushups", "value_type": "count", "aggregation": "sum", **extra},
        )
        assert response.status_code == 422


def test_areas_are_gone_from_the_api(client):
    assert client.get("/areas").status_code == 404
    assert client.get("/views/areas/health").status_code == 404


def test_screen_apps_and_the_journal_mark_their_metrics(client):
    client.post("/screen/categories", json={"slug": "social", "judgment": "waste"})
    client.post("/screen/apps", json={"slug": "instagram", "category": "social"})
    client.get("/journal", params={"as_of": "2026-08-14"})

    origins = {metric["slug"]: metric["origin"] for metric in client.get("/metrics").json()}

    assert origins == {"instagram": "screen", "journal": "journal"}
