EVERY_DAY = {"frequency": "every_day"}


def _create(client, name="Morning pushups", rule=None, **fields):
    body = {"name": name, "rule": rule or EVERY_DAY, "first_day": "2026-08-01", **fields}
    response = client.post("/habits", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_read_a_manual_habit(client):
    created = _create(
        client,
        rule={"frequency": "specific_days", "weekdays": [5, 1]},
        time_of_day="morning",
    )

    assert created["slug"] == "morning-pushups"
    assert created["time_of_day"] == "morning"
    assert created["first_day"] == "2026-08-01"
    assert created["archived_at"] is None
    rule = created["rule"]
    assert (rule["frequency"], rule["weekdays"], rule["check"]) == (
        "specific_days",
        [1, 5],
        "manual",
    )
    assert rule["starts_on"] == "2026-08-01"

    assert client.get("/habits/morning-pushups").json() == created
    assert [habit["slug"] for habit in client.get("/habits").json()] == ["morning-pushups"]


def test_a_data_habit_takes_the_source_defaults_and_names_its_app(client):
    client.post("/screen/categories", json={"slug": "social", "judgment": "waste"})
    client.post(
        "/screen/apps", json={"slug": "instagram", "category": "social", "name": "Instagram"}
    )

    wake = _create(
        client,
        "Wake up early",
        rule={"frequency": "every_day", "check": "data", "source": "wake_time"},
    )
    insta = _create(
        client,
        "Instagram short",
        rule={
            "frequency": "every_day",
            "check": "data",
            "source": "screen_app",
            "source_ref": "instagram",
        },
    )

    assert (wake["rule"]["threshold"], wake["rule"]["value"]) == ("before", 420)
    assert insta["rule"]["source_ref_name"] == "Instagram"
    assert (insta["rule"]["threshold"], insta["rule"]["value"]) == ("at_most", 30)


def test_a_rule_that_does_not_fit_is_refused(client):
    response = client.post(
        "/habits", json={"name": "Run", "rule": {"frequency": "times_a_week", "times": 9}}
    )
    assert response.status_code == 400
    assert "times must be 1 to 7" in response.json()["detail"]


def test_patch_changes_the_rule_from_today_or_for_all_days(client):
    _create(client)

    renamed = client.patch("/habits/morning-pushups", json={"name": "Pushups"})
    assert renamed.json()["name"] == "Pushups"

    changed = client.patch(
        "/habits/morning-pushups",
        json={"rule": {"frequency": "times_a_week", "times": 3}, "apply": "all_days"},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["rule"]["times"] == 3
    assert changed.json()["rule"]["starts_on"] == "2026-08-01"


def test_a_day_is_ticked_and_unticked(client):
    _create(client)

    done = client.put("/habits/morning-pushups/days/2026-08-12", json={"result": "done"})
    assert done.status_code == 200, done.text
    assert done.json() == {"day": "2026-08-12", "result": "done"}

    not_done = client.put("/habits/morning-pushups/days/2026-08-12", json={"result": "not_done"})
    assert not_done.json() == {"day": "2026-08-12", "result": None}

    client.put("/habits/morning-pushups/days/2026-08-13", json={"result": "done"})
    assert client.delete("/habits/morning-pushups/days/2026-08-13").status_code == 204

    early = client.put("/habits/morning-pushups/days/2026-07-31", json={"result": "done"})
    assert early.status_code == 400


def test_archive_restore_and_delete(client):
    _create(client)

    archived = client.post("/habits/morning-pushups/archive")
    assert archived.json()["archived_at"] is not None
    assert client.get("/habits", params={"include_archived": False}).json() == []

    restored = client.post("/habits/morning-pushups/restore")
    assert restored.json()["archived_at"] is None

    assert client.delete("/habits/morning-pushups").status_code == 204
    missing = client.get("/habits/morning-pushups")
    assert missing.status_code == 404
    assert "habit" in missing.json()["detail"]


def test_freezes_for_one_habit_or_all(client):
    _create(client)

    one = client.post(
        "/freezes", json={"habit": "morning-pushups", "start_on": "2026-08-05", "reason": "Sick"}
    )
    assert one.status_code == 201, one.text
    assert one.json()["end_on"] == "2026-08-05"
    every = client.post(
        "/freezes", json={"start_on": "2026-08-10", "end_on": "2026-08-12", "reason": "Holiday"}
    )
    assert every.json()["habit"] is None

    listed = client.get("/freezes", params={"habit": "morning-pushups"}).json()
    assert [row["reason"] for row in listed] == ["Holiday", "Sick"]

    assert client.delete(f"/freezes/{one.json()['id']}").status_code == 204
    assert [row["reason"] for row in client.get("/freezes").json()] == ["Holiday"]
    assert client.delete(f"/freezes/{one.json()['id']}").status_code == 404


def test_the_day_week_and_habit_views(client):
    _create(client, rule={"frequency": "times_a_week", "times": 2}, first_day="2026-11-09")
    client.put("/habits/morning-pushups/days/2026-11-10", json={"result": "done"})

    day = client.get("/views/habits/day", params={"as_of": "2026-11-12"}).json()
    assert (day["day"], day["done"], day["total"]) == ("2026-11-12", 0, 1)
    assert [count["day"] for count in day["week"]][0] == "2026-11-09"
    (row,) = day["rows"]
    assert row["habit"]["slug"] == "morning-pushups"
    assert row["result"] == {"day": "2026-11-12", "status": "open", "reason": None, "value": None}
    assert row["progress"] == {"period": "week", "done": 1, "target": 2}
    assert row["streak"] == {"count": 0, "period": "week"}

    week = client.get("/views/habits/week", params={"as_of": "2026-11-12"}).json()
    statuses = [day["status"] for day in week["rows"][0]["days"]]
    assert statuses == ["blank", "done", "blank", "open", "upcoming", "upcoming", "upcoming"]
    assert week["kept"] == {"done": 1, "target": 2, "share": 0.5}

    detail = client.get("/views/habit/morning-pushups", params={"as_of": "2026-11-12"}).json()
    assert detail["history"][0]["state"] == "running"
    assert detail["kept_last_4_weeks"] == {"done": 0, "target": 0, "share": None}
    assert client.get("/views/habit/nope").status_code == 404
