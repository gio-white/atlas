import typer

from atlas.db import init_db
from atlas.settings import load_settings

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """Personal life-tracking CLI."""


@app.command()
def init() -> None:
    """Create the local SQLite database and schema."""
    settings = load_settings()
    init_db(settings.db_path)
    typer.echo(f"Initialized {settings.db_path}")
