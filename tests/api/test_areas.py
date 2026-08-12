def test_create_and_list_areas(client):
    created = client.post("/areas", json={"slug": "health", "name": "Health"})

    assert created.status_code == 201
    body = created.json()
    assert body["slug"] == "health"
    assert body["name"] == "Health"
    assert body["archived_at"] is None
    assert body["id"] is not None

    listed = client.get("/areas")
    assert listed.status_code == 200
    assert [area["slug"] for area in listed.json()] == ["health"]


def test_duplicate_area_slug_is_conflict(client):
    client.post("/areas", json={"slug": "health"})
    response = client.post("/areas", json={"slug": "health"})

    assert response.status_code == 409
    assert "health" in response.json()["detail"]


def test_invalid_slug_is_bad_request(client):
    response = client.post("/areas", json={"slug": "Health_1"})

    assert response.status_code == 400
    assert "invalid slug" in response.json()["detail"]
