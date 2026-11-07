import json
from pathlib import Path
from typing import Annotated

import typer

from atlas.cli.format import print_imported, print_seeded
from atlas.cli.parse import parse_iso_date
from atlas.cli.session import cli_session, fail
from atlas.db import init_db
from atlas.services import export_all, import_all, seed_demo
from atlas.settings import load_settings

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """Admin CLI: run the app, create the database, and back it up. The rest is the web UI."""


@app.command()
def serve() -> None:
    """Serve the HTTP API and the web UI on localhost."""
    from atlas.api.app import main as serve_api

    serve_api()


@app.command()
def init() -> None:
    """Create the local SQLite database and schema."""
    settings = load_settings()
    init_db(settings.db_path)
    typer.echo(f"Initialized {settings.db_path}")


@app.command()
def seed(
    replace: Annotated[bool, typer.Option("--replace")] = False,
    on: Annotated[str | None, typer.Option("--on")] = None,
) -> None:
    """Load a demo dataset dated relative to today."""
    with cli_session() as session:
        print_seeded(seed_demo(session, as_of=parse_iso_date(on), replace=replace))


@app.command("export")
def export_cmd() -> None:
    """Write a JSON export to stdout."""
    with cli_session() as session:
        typer.echo(json.dumps(export_all(session), indent=2))


@app.command("import")
def import_cmd(
    path: Annotated[Path, typer.Argument(exists=True, readable=True, dir_okay=False)],
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Load a JSON export."""
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(payload, dict):
        fail("import file must be a JSON object")
    with cli_session() as session:
        import_all(session, payload, replace=replace)
        print_imported(str(path), replace=replace)
