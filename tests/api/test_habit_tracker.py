def test_habit_first_create_check_in_and_undo(client):
    created = client.post(
        "/habits",
        json={
            "name": "Read 20 pages",
            "kind": "count",
            "target_value": 20,
            "unit": "pages",
            "time_of_day": "evening",
            "active_from": "2026-08-03",
        },
    )
    assert created.status_code == 201, created.text
    habit = created.json()
    assert habit["slug"] == "read-20-pages"
    assert habit["metric"] == "read-20-pages"
    assert habit["kind"] == "count"
    assert habit["unit"] == "pages"
    assert habit["time_of_day"] == "evening"
    assert habit["archived_at"] is None

    params = {"as_of": "2026-08-10"}
    first = client.post(
        "/habits/read-20-pages/checkins", params=params, json={"amount": 12, "on": "2026-08-10"}
    )
    assert first.status_code == 201, first.text
    status = client.post(
        "/habits/read-20-pages/checkins", params=params, json={"amount": 8, "on": "2026-08-10"}
    ).json()
    assert status["today_value"] == 20.0
    assert status["satisfied"] is True
    assert status["kind"] == "count"
    assert status["effective_target"] == 20.0

    undone = client.delete(
        "/habits/read-20-pages/checkins/last", params={**params, "on": "2026-08-10"}
    )
    assert undone.status_code == 200
    assert undone.json()["today_value"] == 12.0

    detail = client.get("/habits/read-20-pages/detail", params=params).json()
    assert detail["habit"]["slug"] == "read-20-pages"
    assert [row["value"] for row in detail["recent"]] == [12.0]

    future = client.post("/habits/read-20-pages/checkins", params=params, json={"on": "2026-08-11"})
    assert future.status_code == 400


def test_breaks_archive_edit_and_delete(client):
    client.post("/habits", json={"name": "Stretch", "kind": "check", "active_from": "2026-08-03"})
    skip = client.post("/habits/stretch/breaks", json={"start_on": "2026-08-10", "note": "Sick"})
    assert skip.status_code == 201, skip.text
    assert skip.json()["end_on"] == "2026-08-10"
    status = client.get("/habits/stretch/status", params={"as_of": "2026-08-10"}).json()
    assert status["excused"] is True
    assert status["skipped_today"] is True

    calendar = client.get(
        "/views/habits/calendar", params={"period": "week", "as_of": "2026-08-10"}
    ).json()
    monday = calendar["habits"][0]["days"][0]
    assert monday["excused"] is True
    assert monday["satisfied"] is None

    assert client.delete(f"/habits/stretch/breaks/{skip.json()['id']}").status_code == 204
    assert client.get("/habits/stretch/breaks").json() == []

    patched = client.patch(
        "/habits/stretch", json={"name": "Morning stretch", "time_of_day": "morning"}
    )
    assert patched.json()["name"] == "Morning stretch"
    assert patched.json()["time_of_day"] == "morning"

    assert client.post("/habits/stretch/archive").json()["archived_at"] is not None
    board = client.get("/views/habits", params={"as_of": "2026-08-10"}).json()
    assert board["day"] == []
    assert "completion_7d" in board
    assert [
        row["slug"] for row in client.get("/habits", params={"include_archived": False}).json()
    ] == []
    assert client.post("/habits/stretch/unarchive").json()["archived_at"] is None

    assert client.delete("/habits/stretch").status_code == 204
    assert client.get("/habits/stretch").status_code == 404


def test_quit_habit_counts_clean_days(client):
    client.post("/habits", json={"name": "No sugar", "kind": "quit", "active_from": "2026-08-03"})
    params = {"as_of": "2026-08-10"}
    clean = client.get("/habits/no-sugar/status", params=params).json()
    assert clean["current_streak"] == 8
    assert (clean["comparator"], clean["target_value"]) == ("at_most", 0.0)
    slipped = client.post("/habits/no-sugar/checkins", params=params, json={"note": "cake"}).json()
    assert slipped["current_streak"] == 0
    assert slipped["last_entry_on"] == "2026-08-10"
