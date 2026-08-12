from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import Session

from atlas.api.errors import register_exception_handlers
from atlas.api.routers import (
    areas_router,
    entries_router,
    goals_router,
    habits_router,
    metrics_router,
    port_router,
    views_router,
)
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


def create_app(*, session_factory: Callable[[], Session] | None = None) -> FastAPI:
    app = FastAPI(
        title="Atlas",
        description="Personal life-tracking backend",
        lifespan=None if session_factory is not None else lifespan,
    )
    if session_factory is not None:
        app.state.session_factory = session_factory
    register_exception_handlers(app)
    app.include_router(entries_router)
    app.include_router(areas_router)
    app.include_router(metrics_router)
    app.include_router(habits_router)
    app.include_router(goals_router)
    app.include_router(views_router)
    app.include_router(port_router)
    return app


app = create_app()


def main() -> None:
    uvicorn.run(app, host=UVICORN_HOST, port=UVICORN_PORT)


if __name__ == "__main__":
    main()
