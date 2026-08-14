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
