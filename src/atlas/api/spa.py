from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.types import ASGIApp

VITE_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)

_REPO_ROOT = Path(__file__).resolve().parents[3]

# SPA pages whose path is also a GET API route. A browser navigation (reload, typed URL) to
# one of these must get the page, not the JSON the route returns; fetches still reach the API.
SPA_PATHS_SHADOWED_BY_API = frozenset({"/tasks", "/journal"})


def resolve_spa_dir(candidates: list[Path] | None = None) -> Path | None:
    paths = candidates or [
        Path.cwd() / "web" / "dist",
        _REPO_ROOT / "web" / "dist",
    ]
    for candidate in paths:
        if (candidate / "index.html").is_file():
            return candidate
    return None


class SpaFallbackMiddleware(BaseHTTPMiddleware):
    """Serve `web/dist` for GET 404s so UI routes do not steal API paths."""

    def __init__(self, app: ASGIApp, dist: Path) -> None:
        super().__init__(app)
        self.dist = dist.resolve()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        index = self.dist / "index.html"
        if (
            request.method == "GET"
            and request.url.path in SPA_PATHS_SHADOWED_BY_API
            and _is_document_request(request)
            and index.is_file()
        ):
            return FileResponse(index)
        response = await call_next(request)
        if request.method != "GET" or response.status_code != 404:
            return response
        relative = request.url.path.lstrip("/")
        target = (self.dist / relative).resolve()
        try:
            target.relative_to(self.dist)
        except ValueError:
            return response
        if relative and target.is_file():
            return FileResponse(target)
        if index.is_file():
            return FileResponse(index)
        return response


def _is_document_request(request: Request) -> bool:
    if request.headers.get("sec-fetch-dest") == "document":
        return True
    return "text/html" in request.headers.get("accept", "")


def mount_spa(app: FastAPI, dist: Path) -> None:
    app.add_middleware(SpaFallbackMiddleware, dist=dist)
