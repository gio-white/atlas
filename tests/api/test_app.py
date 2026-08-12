import uvicorn

from atlas.api.app import UVICORN_HOST, main


def test_openapi_lists_the_implemented_paths(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/entries" in paths
    assert "/areas" in paths
    assert "/metrics" in paths
    assert "/habits" in paths
    assert "/habits/{slug}/status" in paths
    assert "/goals" in paths
    assert "/goals/{slug}/progress" in paths
    assert "/views/today" in paths
    assert "/views/week" in paths
    assert "/views/areas/{slug}" in paths
    assert "/export" in paths
    assert "/import" in paths


def test_uvicorn_entrypoint_binds_localhost(monkeypatch):
    called: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        called["args"] = args
        called.update(kwargs)

    monkeypatch.setattr(uvicorn, "run", fake_run)
    main()

    assert called["host"] == UVICORN_HOST == "127.0.0.1"
    assert called["port"] == 8000
