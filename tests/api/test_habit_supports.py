def ok(response, status: int = 200):
    assert response.status_code == status, response.text
    return response.json() if response.content else None


def _setup(client) -> dict[str, int]:
    ok(client.post("/habits", json={"name": "Read", "rule": {"frequency": "every_day"}}), 201)
    ambition = ok(client.post("/ambitions", json={"title": "Grow"}), 201)
    goal = ok(client.post("/goals", json={"title": "Ship", "ambition_id": ambition["id"]}), 201)
    milestone = ok(client.post("/milestones", json={"title": "Beta", "goal_id": goal["id"]}), 201)
    chapter = ok(
        client.post("/chapters", json={"title": "Basics", "milestone_id": milestone["id"]}), 201
    )
    task = ok(
        client.post(
            "/tasks",
            json={"title": "Read", "parent_kind": "chapter", "parent_id": chapter["id"]},
        ),
        201,
    )
    side_quest = ok(client.post("/side-quests", json={"title": "Trip"}), 201)
    return {
        "ambition": ambition["id"],
        "goal": goal["id"],
        "milestone": milestone["id"],
        "chapter": chapter["id"],
        "task": task["id"],
        "side_quest": side_quest["id"],
    }


def test_read_add_and_remove_links_at_every_level(client):
    ids = _setup(client)
    for kind, item_id in ids.items():
        link = ok(client.post("/habits/read/supports", json={"kind": kind, "id": item_id}), 201)
        assert (link["kind"], link["id"]) == (kind, item_id)

    supports = ok(client.get("/habits/read/supports"))
    assert [row["kind"] for row in supports] == [
        "ambition",
        "goal",
        "milestone",
        "side_quest",
        "chapter",
        "task",
    ]
    assert [ref["title"] for ref in supports[-1]["path"]] == ["Grow", "Ship", "Beta", "Basics"]

    ok(client.delete(f"/habits/read/supports/goal/{ids['goal']}"), 204)
    assert len(ok(client.get("/habits/read/supports"))) == 5
    assert client.delete(f"/habits/read/supports/goal/{ids['goal']}").status_code == 404


def test_errors(client):
    ids = _setup(client)
    body = {"kind": "goal", "id": ids["goal"]}
    ok(client.post("/habits/read/supports", json=body), 201)
    assert client.post("/habits/read/supports", json=body).status_code == 409
    assert client.post("/habits/read/supports", json={"kind": "goal", "id": 999}).status_code == 404
    assert client.post("/habits/read/supports", json={"kind": "area", "id": 1}).status_code == 422
    assert client.post("/habits/nope/supports", json=body).status_code == 404


def test_each_item_lists_the_habits_that_support_it(client):
    ids = _setup(client)
    ok(client.post("/habits/read/supports", json={"kind": "task", "id": ids["task"]}), 201)
    paths = {
        "ambition": "/ambitions",
        "goal": "/goals",
        "milestone": "/milestones",
        "chapter": "/chapters",
        "task": "/tasks",
    }
    for kind, prefix in paths.items():
        rows = ok(client.get(f"{prefix}/{ids[kind]}/habits"))
        assert [(row["slug"], row["linked_to"]["kind"]) for row in rows] == [("read", "task")]
        assert rows[0]["direct"] is (kind == "task")
    assert ok(client.get(f"/side-quests/{ids['side_quest']}/habits")) == []


def test_linking_leaves_goal_progress_alone(client):
    ids = _setup(client)
    before = ok(client.get(f"/goals/{ids['goal']}"))
    ok(client.post("/habits/read/supports", json={"kind": "goal", "id": ids["goal"]}), 201)
    assert ok(client.get(f"/goals/{ids['goal']}")) == before
