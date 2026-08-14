def test_create_list_and_complete_task(client):
    created = client.post(
        "/tasks",
        json={"title": "Family time", "bucket": "today", "priority": "high"},
    )
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]
    listed = client.get("/tasks")
    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "Family time"

    patched = client.patch(f"/tasks/{task_id}", json={"done": True})
    assert patched.status_code == 200
    assert patched.json()["done_at"] is not None
    assert client.get("/tasks").json() == []
    assert client.get("/tasks", params={"include_done": True}).json()[0]["id"] == task_id


def test_create_task_linked_to_goal(client, seed_health):
    goal = client.post(
        "/goals",
        json={
            "slug": "workout-week",
            "area": "health",
            "kind": "milestone",
            "start_on": "2026-08-10",
            "due_on": "2026-08-16",
        },
    )
    assert goal.status_code == 201
    created = client.post("/tasks", json={"title": "Pushups", "goal": "workout-week"})
    assert created.status_code == 201, created.text
    assert created.json()["goal"] == "workout-week"
    listed = client.get("/tasks", params={"goal": "workout-week"})
    assert [task["title"] for task in listed.json()] == ["Pushups"]
