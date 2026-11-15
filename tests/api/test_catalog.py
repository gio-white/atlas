def test_get_patch_and_archive_metric(client, seed_health):
    fetched = client.get("/metrics/pushups")
    assert fetched.status_code == 200
    assert fetched.json()["origin"] == "manual"
    assert "area" not in fetched.json()

    patched = client.patch("/metrics/pushups", json={"name": "Push-ups", "unit": "reps"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Push-ups"
    assert patched.json()["value_type"] == "count"

    archived = client.post("/metrics/pushups/archive")
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None


def test_unknown_catalog_slug_is_not_found(client):
    assert client.get("/metrics/missing").status_code == 404
    assert client.get("/habits/missing").status_code == 404
