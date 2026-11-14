from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def utc_zone(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def ok(response, status: int = 200):
    assert response.status_code == status, response.text
    return response.json()


def test_quest_tree_crud_and_views(client):
    ambition = ok(client.post("/ambitions", json={"title": "Become a better engineer"}), 201)
    assert ambition["progress"] is None
    assert ambition["status"] == "active"
    goal = ok(
        client.post(
            "/goals",
            json={
                "title": "Move to Copenhagen",
                "ambition_id": ambition["id"],
                "success_description": "Living there",
                "due_on": "2027-06-30",
            },
        ),
        201,
    )
    milestone = ok(client.post("/milestones", json={"goal_id": goal["id"], "title": "Job"}), 201)
    chapter = ok(
        client.post("/chapters", json={"milestone_id": milestone["id"], "title": "Rust"}), 201
    )
    assert chapter["state"] == "empty"
    task = ok(
        client.post(
            "/tasks",
            json={
                "title": "Understand ownership",
                "parent_kind": "chapter",
                "parent_id": chapter["id"],
                "estimate_minutes": 120,
                "priority": "high",
            },
        ),
        201,
    )
    assert [item["kind"] for item in task["path"]] == ["ambition", "goal", "milestone", "chapter"]
    assert task["blocks"] == []

    tree = ok(client.get(f"/views/goals/{goal['id']}"))
    assert tree["goal"]["path"] == [
        {"kind": "ambition", "id": ambition["id"], "title": "Become a better engineer"}
    ]
    assert tree["milestones"][0]["chapters"][0]["tasks"][0]["id"] == task["id"]
    assert tree["goal"]["next_action"]["id"] == task["id"]

    main = ok(client.get("/views/main-quests"))
    assert main["ambitions"][0]["goals"][0]["milestone_count"] == 1
    assert main["independent_goals"] == []
    section = ok(client.get(f"/views/ambitions/{ambition['id']}"))
    assert section["ambition"]["goal_count"] == 1

    assert ok(client.get("/ambitions"))[0]["id"] == ambition["id"]
    assert ok(client.get("/goals", params={"ambition_id": ambition["id"]}))[0]["id"] == goal["id"]
    assert ok(client.get(f"/milestones/{milestone['id']}"))["chapter_count"] == 1
    assert ok(client.get(f"/chapters/{chapter['id']}"))["task_count"] == 1
    renamed = ok(client.patch(f"/goals/{goal['id']}", json={"title": "Move abroad"}))
    assert renamed["title"] == "Move abroad"
    unparented = ok(client.patch(f"/goals/{goal['id']}", json={"ambition_id": None}))
    assert unparented["ambition_id"] is None


def test_side_quests_inbox_organize_and_promote(client):
    side = ok(client.post("/side-quests", json={"title": "Tax declaration"}), 201)
    captured = ok(client.post("/tasks", json={"title": "Find payslips"}), 201)
    assert captured["inbox"] is True
    inbox = ok(client.get("/views/inbox"))
    assert (inbox["count"], inbox["tasks"][0]["id"]) == (1, captured["id"])

    organized = ok(
        client.post(
            f"/tasks/{captured['id']}/organize",
            json={"parent_kind": "side_quest", "parent_id": side["id"]},
        )
    )
    assert organized["id"] == captured["id"]
    assert organized["inbox"] is False
    assert ok(client.get("/views/inbox"))["count"] == 0
    tree = ok(client.get(f"/views/side-quests/{side['id']}"))
    assert [item["id"] for item in tree["tasks"]] == [captured["id"]]

    errand = ok(client.post("/tasks", json={"title": "Renew passport", "standalone": True}), 201)
    listing = ok(client.get("/views/side-quests"))
    assert [item["id"] for item in listing["standalone_tasks"]] == [errand["id"]]
    assert [item["id"] for item in listing["side_quests"]] == [side["id"]]
    assert ok(client.get("/side-quests"))[0]["title"] == "Tax declaration"

    idea = ok(client.post("/tasks", json={"title": "Learn Danish", "description": "B1"}), 201)
    promoted = ok(client.post(f"/tasks/{idea['id']}/promote", json={"kind": "goal"}), 201)
    assert promoted["kind"] == "goal"
    goal = ok(client.get(f"/goals/{promoted['id']}"))
    assert (goal["title"], goal["description"]) == ("Learn Danish", "B1")
    assert client.get(f"/tasks/{idea['id']}").status_code == 404


def test_completion_override_and_reopen(client):
    goal = ok(client.post("/goals", json={"title": "Ship"}), 201)
    open_task = ok(
        client.post(
            "/tasks", json={"title": "Write", "parent_kind": "goal", "parent_id": goal["id"]}
        ),
        201,
    )
    refused = client.post(f"/goals/{goal['id']}/complete")
    assert refused.status_code == 409
    assert "override" in refused.json()["detail"]
    completed = ok(client.post(f"/goals/{goal['id']}/complete", json={"override": True}))
    assert completed["status"] == "completed"
    assert completed["completed_with_open_items"] is True
    assert completed["open_children"] == [{"kind": "task", "id": open_task["id"], "title": "Write"}]
    assert ok(client.get(f"/tasks/{open_task['id']}"))["status"] == "todo"
    reopened = ok(client.post(f"/goals/{goal['id']}/reopen"))
    assert reopened["status"] == "active"

    done = ok(client.patch(f"/tasks/{open_task['id']}", json={"status": "completed"}))
    assert done["completed_at"] is not None
    eligible = ok(client.get(f"/goals/{goal['id']}"))
    assert eligible["eligible"] is True
    assert eligible["progress"] == 1.0
    assert eligible["status"] == "active"
    assert ok(client.post(f"/goals/{goal['id']}/complete"))["completed_with_open_items"] is False


def test_time_blocks_and_execution_views(client):
    task = ok(client.post("/tasks", json={"title": "Study", "standalone": True}), 201)
    now = datetime.now(UTC).replace(microsecond=0)
    start = now - timedelta(hours=3)
    block = ok(
        client.post(
            "/time-blocks",
            json={
                "task_id": task["id"],
                "start_at": start.isoformat(),
                "end_at": (start + timedelta(hours=1)).isoformat(),
            },
        ),
        201,
    )
    assert block["unconfirmed"] is True
    assert block["minutes"] == 60
    later = ok(
        client.post(
            "/time-blocks",
            json={
                "task_id": task["id"],
                "start_at": (now + timedelta(hours=2)).isoformat(),
                "end_at": (now + timedelta(hours=3)).isoformat(),
            },
        ),
        201,
    )
    moved = ok(
        client.patch(
            f"/time-blocks/{later['id']}",
            json={"end_at": (now + timedelta(hours=4)).isoformat()},
        )
    )
    assert moved["minutes"] == 120
    listed = ok(client.get("/time-blocks", params={"task_id": task["id"]}))
    assert [item["id"] for item in listed] == [block["id"], later["id"]]

    today = ok(client.get("/views/today"))
    assert [item["block"]["id"] for item in today["unconfirmed"]] == [block["id"]]
    calendar = ok(
        client.get(
            "/views/calendar",
            params={
                "start": (now - timedelta(days=1)).isoformat(),
                "end": (now + timedelta(days=1)).isoformat(),
            },
        )
    )
    assert {item["block"]["id"] for item in calendar["blocks"]} == {block["id"], later["id"]}

    completed = ok(client.post(f"/time-blocks/{block['id']}/complete"))
    assert completed["status"] == "completed"
    assert ok(client.get(f"/tasks/{task['id']}"))["status"] == "in_progress"
    cancelled = ok(client.post(f"/time-blocks/{later['id']}/cancel"))
    assert cancelled["status"] == "cancelled"
    detail = ok(client.get(f"/tasks/{task['id']}"))
    assert detail["planned_minutes"] == 60
    assert len(detail["blocks"]) == 2
    assert client.delete(f"/time-blocks/{later['id']}").status_code == 204
    assert client.post(f"/time-blocks/{later['id']}/complete").status_code == 404


def test_error_mapping(client):
    assert client.get("/goals/999").status_code == 404
    assert client.get("/views/goals/999").status_code == 404
    assert client.post("/tasks/999/organize", json={"standalone": True}).status_code == 404
    assert client.post("/milestones", json={"goal_id": 999, "title": "x"}).status_code == 400
    archived = ok(client.post("/side-quests", json={"title": "Old"}), 201)
    ok(client.patch(f"/side-quests/{archived['id']}", json={"archived": True}))
    refused = client.post(
        "/tasks", json={"title": "x", "parent_kind": "side_quest", "parent_id": archived["id"]}
    )
    assert refused.status_code == 400
    assert "archived" in refused.json()["detail"]
    goal = ok(client.post("/goals", json={"title": "Ship"}), 201)
    ok(client.post("/milestones", json={"goal_id": goal["id"], "title": "Beta"}), 201)
    assert client.delete(f"/goals/{goal['id']}").status_code == 409
    empty = ok(client.post("/ambitions", json={"title": "Empty"}), 201)
    assert client.delete(f"/ambitions/{empty['id']}").status_code == 204
    assert client.post("/chapters", json={"title": "Orphan"}).status_code == 400
    assert client.post("/tasks", json={"title": "x", "estimate_minutes": 0}).status_code == 422
    assert client.post("/goals", json={"title": "x", "weight": 0}).status_code == 422
    assert client.post("/goals", json={"title": "  "}).status_code == 400

    task = ok(client.post("/tasks", json={"title": "Study"}), 201)
    now = datetime.now(UTC)
    bad = client.post(
        "/time-blocks",
        json={"task_id": task["id"], "start_at": now.isoformat(), "end_at": now.isoformat()},
    )
    assert bad.status_code == 400
    ok(
        client.post(
            "/time-blocks",
            json={
                "task_id": task["id"],
                "start_at": now.isoformat(),
                "end_at": (now + timedelta(hours=1)).isoformat(),
            },
        ),
        201,
    )
    promote = client.post(f"/tasks/{task['id']}/promote", json={"kind": "side_quest"})
    assert promote.status_code == 400
    assert "organize it instead" in promote.json()["detail"]
    assert client.delete(f"/tasks/{task['id']}").status_code == 409


def test_a_session_can_be_marked_as_didnt_happen_once_it_has_started(client):
    task = ok(client.post("/tasks", json={"title": "Study", "standalone": True}), 201)
    now = datetime.now(UTC).replace(microsecond=0)

    def session_at(start):
        body = {
            "task_id": task["id"],
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat(),
        }
        return ok(client.post("/time-blocks", json=body), 201)

    past = session_at(now - timedelta(hours=3))
    future = session_at(now + timedelta(hours=3))

    missed = ok(client.post(f"/time-blocks/{past['id']}/miss"))
    assert missed["status"] == "missed"
    assert missed["unconfirmed"] is False
    assert client.post(f"/time-blocks/{future['id']}/miss").status_code == 400
    assert client.post("/time-blocks/99999/miss").status_code == 404
    assert ok(client.get("/views/today"))["unconfirmed"] == []
    assert ok(client.get(f"/tasks/{task['id']}"))["planned_minutes"] == 60
