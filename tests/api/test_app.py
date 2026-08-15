import uvicorn

from atlas.api.app import UVICORN_HOST, main

IMPLEMENTED_PATHS = frozenset(
    {
        "/entries",
        "/entries/{entry_id}",
        "/areas",
        "/areas/{slug}",
        "/areas/{slug}/archive",
        "/metrics",
        "/metrics/{slug}",
        "/metrics/{slug}/archive",
        "/habits",
        "/habits/{slug}",
        "/habits/{slug}/status",
        "/goals",
        "/goals/{slug}",
        "/goals/{slug}/progress",
        "/goals/{slug}/milestones/{name}/toggle",
        "/views/today",
        "/views/week",
        "/views/home",
        "/views/goals",
        "/views/habits",
        "/views/areas/{slug}",
        "/screen/view",
        "/screen/dashboard",
        "/screen/categories",
        "/screen/categories/{slug}",
        "/screen/apps",
        "/screen/apps/{slug}",
        "/screen/budgets",
        "/screen/budgets/{slug}",
        "/screen/devices",
        "/screen/devices/{slug}",
        "/screen/sessions",
        "/screen/sessions/{session_id}",
        "/updates",
        "/slips",
        "/tasks",
        "/tasks/{task_id}",
        "/journal",
        "/entertainment/view",
        "/entertainment/dashboard",
        "/entertainment/topics",
        "/entertainment/topics/{slug}",
        "/entertainment/titles",
        "/entertainment/titles/{slug}",
        "/entertainment/titles/{slug}/image",
        "/export",
        "/import",
    }
)


def test_openapi_lists_the_implemented_paths(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    missing = sorted(IMPLEMENTED_PATHS - paths.keys())
    assert missing == []
    extra = sorted(path for path in paths if path not in IMPLEMENTED_PATHS)
    assert extra == []


def test_uvicorn_entrypoint_binds_localhost(monkeypatch):
    called: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        called["args"] = args
        called.update(kwargs)

    monkeypatch.setattr(uvicorn, "run", fake_run)
    main()

    assert called["host"] == UVICORN_HOST == "127.0.0.1"
    assert called["port"] == 8000
