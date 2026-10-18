import pytest


@pytest.fixture(autouse=True)
def _utc(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def test_log_and_review_a_night(client):
    created = client.post(
        "/sleep/sessions",
        json={
            "started_at": "2026-08-12T23:00:00Z",
            "ended_at": "2026-08-13T07:00:00Z",
            "stages": [
                {
                    "stage": "light",
                    "started_at": "2026-08-12T23:00:00Z",
                    "ended_at": "2026-08-13T02:00:00Z",
                },
                {
                    "stage": "deep",
                    "started_at": "2026-08-13T02:00:00Z",
                    "ended_at": "2026-08-13T03:00:00Z",
                },
            ],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["occurred_on"] == "2026-08-13"
    assert body["source"] == "api"
    assert [stage["stage"] for stage in body["stages"]] == ["light", "deep"]

    view = client.get("/sleep/view", params={"as_of": "2026-08-13"})
    assert view.status_code == 200, view.text
    night = view.json()["night"]
    assert night["bed_offset"] == -60
    assert night["stages"]["deep"] == 60
    assert len(view.json()["days"]) == 7

    listed = client.get("/sleep/sessions", params={"occurred_on": "2026-08-13"})
    assert [row["id"] for row in listed.json()] == [body["id"]]

    removed = client.delete(f"/sleep/sessions/{body['id']}")
    assert removed.status_code == 204
    assert client.get(f"/sleep/sessions/{body['id']}").status_code == 404


def test_rejects_a_night_that_ends_before_it_starts(client):
    response = client.post(
        "/sleep/sessions",
        json={"started_at": "2026-08-13T07:00:00Z", "ended_at": "2026-08-12T23:00:00Z"},
    )
    assert response.status_code == 400
