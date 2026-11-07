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


def _post_night(client, day: int, bed_hour: int = 23):
    response = client.post(
        "/sleep/sessions",
        json={
            "started_at": f"2026-08-{day - 1:02d}T{bed_hour:02d}:00:00Z",
            "ended_at": f"2026-08-{day:02d}T07:00:00Z",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_ingestion_door_accepts_nights_and_view_reports_freshness(client):
    assert (
        client.get("/sleep/view", params={"as_of": "2026-08-13"}).json()["last_recorded_at"] is None
    )
    _post_night(client, 12, bed_hour=22)
    _post_night(client, 13)

    view = client.get("/sleep/view", params={"as_of": "2026-08-13"}).json()

    assert view["last_recorded_at"] is not None
    assert view["nights_logged"] == 2
    assert view["bed_spread"] == 30
    assert view["wake_spread"] == 0


def test_sleep_view_takes_a_range_of_days(client):
    _post_night(client, 13)

    month = client.get("/sleep/view", params={"as_of": "2026-08-13", "days": 30}).json()

    assert len(month["days"]) == 30
    assert month["range_start"] == "2026-07-15"
    assert [day["night"] is None for day in month["days"]].count(False) == 1
    assert client.get("/sleep/view", params={"days": 0}).status_code == 422
    assert client.get("/sleep/view", params={"days": 367}).status_code == 422
