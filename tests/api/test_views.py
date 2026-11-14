def test_week_so_far_view(client):
    response = client.get("/views/week-so-far", params={"as_of": "2026-08-13"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["week_start"] == "2026-08-10"
    assert body["sessions_total"] == 0
    assert body["habits_kept_share"] is None
    assert set(body) >= {"sleep_average_minutes", "sleep_nights", "screen_score"}


def test_this_week_view(client):
    response = client.get("/views/this-week", params={"as_of": "2026-08-13"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["week_start"], body["week_end"], body["complete"]) == (
        "2026-08-10",
        "2026-08-16",
        False,
    )
    assert body["previous"]["as_of"] == "2026-08-06"
    assert body["current"]["tasks_completed"] == 0
    assert body["habits"] == []


def test_this_week_lists_active_habits_by_name(client):
    client.post("/habits", json={"name": "Read", "rule": {"frequency": "every_day"}})

    body = client.get("/views/this-week", params={"as_of": "2026-08-13"}).json()

    assert body["habits"] == [{"slug": "read", "name": "Read"}]
