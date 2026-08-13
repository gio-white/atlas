from pathlib import Path

from fastapi.testclient import TestClient

from atlas.api.app import create_app
from atlas.api.spa import VITE_ORIGINS, resolve_spa_dir
from atlas.db import create_memory_engine, init_schema, make_session_factory


def _client(spa_dir: Path | None = None) -> TestClient:
    engine = create_memory_engine()
    init_schema(engine)
    return TestClient(create_app(session_factory=make_session_factory(engine), spa_dir=spa_dir))


def test_cors_allows_vite_origin(client):
    response = client.options(
        "/areas",
        headers={
            "Origin": VITE_ORIGINS[0],
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in {200, 204}
    assert response.headers["access-control-allow-origin"] == VITE_ORIGINS[0]


def test_cors_rejects_non_vite_origin(client):
    response = client.options(
        "/areas",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_spa_fallback_serves_index_for_ui_routes(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Atlas</title>", encoding="utf-8")
    (dist / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('atlas')", encoding="utf-8")

    client = _client(spa_dir=dist)

    home = client.get("/")
    assert home.status_code == 200
    assert "Atlas" in home.text
    assert "text/html" in home.headers["content-type"]

    index = client.get("/week")
    assert index.status_code == 200
    assert "Atlas" in index.text
    assert "text/html" in index.headers["content-type"]

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert "atlas" in asset.text

    static = client.get("/favicon.svg")
    assert static.status_code == 200
    assert "<svg" in static.text


def test_spa_does_not_shadow_api_routes(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Atlas</title>", encoding="utf-8")

    client = _client(spa_dir=dist)
    created = client.post("/areas", json={"slug": "health", "name": "Health"})
    assert created.status_code == 201, created.text

    listed = client.get("/areas")
    assert listed.status_code == 200
    assert listed.json()[0]["slug"] == "health"
    assert listed.headers["content-type"].startswith("application/json")

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower() or "openapi" in docs.text.lower()


def test_unknown_path_is_404_when_spa_is_absent(client):
    response = client.get("/week")
    assert response.status_code == 404


def test_resolve_spa_dir_returns_none_without_index(tmp_path):
    assert resolve_spa_dir([tmp_path / "dist"]) is None


def test_resolve_spa_dir_finds_index(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assert resolve_spa_dir([dist]) == dist
