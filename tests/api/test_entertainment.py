from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.domain import EntertainmentKind, EntertainmentStatus

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _topic(client, slug="physics"):
    response = client.post("/entertainment/topics", json={"slug": slug})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list_titles(client):
    _topic(client)
    created = client.post(
        "/entertainment/titles",
        json={
            "slug": "interstellar",
            "kind": "film",
            "name": "Interstellar",
            "creator": "Christopher Nolan",
            "recommended_by": "Alex",
            "status": "done",
            "finished_on": "2026-08-12",
            "topics": ["physics"],
            "image_url": "https://example.com/interstellar.jpg",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["kind"] == EntertainmentKind.FILM
    assert body["status"] == EntertainmentStatus.DONE
    assert body["topics"][0]["slug"] == "physics"
    assert body["image"] == "https://example.com/interstellar.jpg"

    listed = client.get("/entertainment/titles", params={"kind": "film", "topic": "physics"})
    assert listed.status_code == 200
    assert [row["slug"] for row in listed.json()] == ["interstellar"]


def test_dashboard_and_view(client):
    _topic(client, "programming")
    client.post(
        "/entertainment/titles",
        json={
            "slug": "lex",
            "kind": "podcast",
            "status": "done",
            "finished_on": "2026-08-13",
            "topics": ["programming"],
        },
    )
    client.post(
        "/entertainment/titles",
        json={"slug": "office", "kind": "series", "status": "in_progress"},
    )
    dash = client.get("/entertainment/dashboard", params={"period": "week", "as_of": "2026-08-14"})
    assert dash.status_code == 200, dash.text
    payload = dash.json()
    assert payload["finished_in_range"] == 1
    assert payload["in_progress"] == 1
    assert payload["library"]["done"][0]["slug"] == "lex"

    view = client.get("/entertainment/view", params={"as_of": "2026-08-14"})
    assert view.status_code == 200
    assert view.json()["finished_this_week"] == 1
    assert view.json()["last_finished"]["slug"] == "lex"


def test_image_upload_round_trip(client):
    client.post("/entertainment/titles", json={"slug": "clip", "kind": "video"})
    uploaded = client.put(
        "/entertainment/titles/clip/image",
        files={"file": ("poster.png", PNG, "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["image"] == "/entertainment/titles/clip/image"

    downloaded = client.get("/entertainment/titles/clip/image")
    assert downloaded.status_code == 200
    assert downloaded.content == PNG
    assert downloaded.headers["content-type"].startswith("image/png")

    cleared = client.delete("/entertainment/titles/clip/image")
    assert cleared.status_code == 200
    assert cleared.json()["image"] is None
    missing = client.get("/entertainment/titles/clip/image")
    assert missing.status_code == 404


def test_export_includes_entertainment(client):
    _topic(client, "math")
    client.post(
        "/entertainment/titles",
        json={"slug": "linear-algebra", "kind": "video", "topics": ["math"]},
    )
    exported = client.get("/export")
    assert exported.status_code == 200
    payload = exported.json()
    assert payload["schema_version"] == CURRENT_SCHEMA_VERSION
    assert [row["slug"] for row in payload["entertainment_topics"]] == ["math"]
    assert payload["entertainment_titles"][0]["topics"] == ["math"]
    assert payload["entries"] == []
