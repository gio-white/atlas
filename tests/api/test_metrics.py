def test_create_metric_accepts_an_area_slug(client, seed_health):
    listed = client.get("/metrics", params={"area": "health"})
    assert listed.status_code == 200
    slugs = {metric["slug"] for metric in listed.json()}
    assert slugs == {"meditated", "pushups", "weight"}
    pushups = next(metric for metric in listed.json() if metric["slug"] == "pushups")
    assert pushups["area"] == "health"
    assert pushups["value_type"] == "count"
    assert pushups["aggregation"] == "sum"


def test_create_metric_for_unknown_area_is_not_found(client):
    response = client.post(
        "/metrics",
        json={
            "slug": "pushups",
            "area": "missing",
            "value_type": "count",
            "aggregation": "sum",
        },
    )

    assert response.status_code == 404
    assert "area" in response.json()["detail"]
