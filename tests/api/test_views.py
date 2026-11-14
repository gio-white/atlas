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


def test_week_so_far_view(client):
    response = client.get("/views/week-so-far", params={"as_of": "2026-08-13"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["week_start"] == "2026-08-10"
    assert body["sessions_total"] == 0
    assert body["habits_kept_share"] is None
    assert set(body) >= {"sleep_average_minutes", "sleep_nights", "screen_score"}
