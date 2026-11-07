"""Docs drift: the API tables under docs/ and the FastAPI app list the same routes."""

import re
from pathlib import Path

from atlas.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SKIPPED_DIRS = {"plans", "changelog"}
ROW = re.compile(r"^\|\s*`(GET|POST|PUT|PATCH|DELETE)`\s*\|([^|]+)\|")
PATH = re.compile(r"`(/[^`]*)`")
PARAM = re.compile(r"\{[^}]+\}")


def normalize(method: str, path: str) -> str:
    return f"{method} {PARAM.sub('{}', path)}"


def expand(cell: str) -> list[str]:
    """`/habits/{slug}/archive` / `/unarchive` → both full paths."""
    paths = PATH.findall(cell)
    if not paths:
        return []
    first = paths[0]
    expanded = [first]
    for extra in paths[1:]:
        if extra.count("/") == 1:
            expanded.append(first.rsplit("/", 1)[0] + extra)
        else:
            expanded.append(extra)
    return expanded


def documented_routes(docs: Path = DOCS) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(docs.rglob("*.md")):
        if SKIPPED_DIRS & set(path.relative_to(docs).parts):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = ROW.match(line)
            if match:
                for route in expand(match.group(2)):
                    found.setdefault(normalize(match.group(1), route), path)
    return found


def app_routes(app=None) -> set[str]:
    schema = (app or create_app(session_factory=lambda: None)).openapi()
    return {
        normalize(method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
    }


def test_every_api_route_is_documented():
    missing = sorted(app_routes() - documented_routes().keys())
    assert not missing, (
        "routes missing from the API tables in docs/domain/*.md (or docs/architecture/cli.md): "
        f"{missing}"
    )


def test_every_documented_route_exists():
    documented = documented_routes()
    stale = sorted(
        f"{route} ({documented[route].relative_to(ROOT)})"
        for route in documented.keys() - app_routes()
    )
    assert not stale, f"documented routes that the API does not serve: {stale}"


def test_drift_check_catches_an_undocumented_route():
    app = create_app(session_factory=lambda: None)

    @app.get("/undocumented-probe")
    def probe() -> dict[str, str]:
        return {}

    assert "GET /undocumented-probe" in app_routes(app) - documented_routes().keys()


def test_expand_resolves_shorthand_paths():
    assert expand("`/habits/{slug}/archive` / `/unarchive`") == [
        "/habits/{slug}/archive",
        "/habits/{slug}/unarchive",
    ]
