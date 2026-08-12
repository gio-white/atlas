from collections.abc import Iterator
from contextlib import contextmanager
from typing import NoReturn

import typer
from rich.console import Console
from sqlmodel import Session

from atlas.db import init_db, make_session_factory
from atlas.services import AlreadyExistsError, NotFoundError, ValidationError
from atlas.settings import SettingsError, load_settings

err_console = Console(stderr=True)


def fail(message: str) -> NoReturn:
    err_console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


@contextmanager
def cli_session() -> Iterator[Session]:
    try:
        factory = make_session_factory(init_db(load_settings().db_path))
        with factory() as session:
            yield session
    except (AlreadyExistsError, NotFoundError, SettingsError, ValidationError) as exc:
        fail(str(exc))
