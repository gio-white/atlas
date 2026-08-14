from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from atlas.api.errors import register_exception_handlers
from atlas.api.routers import (
    areas_router,
    entertainment_router,
    entries_router,
    goals_router,
    habits_router,
    journal_router,
    metrics_router,
    port_router,
    screen_router,
    slips_router,
    tasks_router,
    updates_router,
    views_router,
)
from atlas.api.spa import VITE_ORIGINS, mount_spa, resolve_spa_dir
from atlas.db import init_db, make_session_factory
from atlas.settings import load_settings

UVICORN_HOST = "127.0.0.1"
UVICORN_PORT = 8000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = load_settings()
    engine = init_db(settings.db_path)
    app.state.session_factory = make_session_factory(engine)
    yield


def create_app(
    *,
    session_factory: Callable[[], Session] | None = None,
    spa_dir: Path | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Atlas",
        description="Personal life-tracking backend",
        lifespan=None if session_factory is not None else lifespan,
    )
    if session_factory is not None:
        app.state.session_factory = session_factory
    register_exception_handlers(app)
    app.include_router(entries_router)
    app.include_router(entertainment_router)
    app.include_router(areas_router)
    app.include_router(metrics_router)
    app.include_router(habits_router)
    app.include_router(goals_router)
    app.include_router(views_router)
    app.include_router(screen_router)
    app.include_router(updates_router)
    app.include_router(slips_router)
    app.include_router(tasks_router)
    app.include_router(journal_router)
    app.include_router(port_router)
    if spa_dir is not None:
        mount_spa(app, spa_dir)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(VITE_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app(spa_dir=resolve_spa_dir())


def main() -> None:
    uvicorn.run(app, host=UVICORN_HOST, port=UVICORN_PORT)


if __name__ == "__main__":
    main()
