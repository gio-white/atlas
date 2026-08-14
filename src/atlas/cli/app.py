import json
from pathlib import Path
from typing import Annotated

import typer
from sqlmodel import Session

from atlas.cli.format import (
    print_amended,
    print_created,
    print_deleted,
    print_imported,
    print_logged,
    print_screen_logged,
    print_seeded,
)
from atlas.cli.lookup import resolve_metric_slug
from atlas.cli.parse import (
    comparator_and_target,
    comparator_from_flags,
    measure_from_flag,
    parse_iso_date,
    parse_iso_datetime,
    parse_log_value,
    parse_weekdays,
    require_iso_date,
    slugify,
)
from atlas.cli.session import cli_session, fail
from atlas.db import init_db
from atlas.domain import (
    Aggregation,
    Direction,
    GoalHorizon,
    GoalKind,
    Period,
    TaskBucket,
    TaskPriority,
    ValueType,
)
from atlas.services import (
    amend_entry,
    create_area,
    create_goal,
    create_habit,
    create_metric,
    create_task,
    delete_entry,
    export_all,
    get_metric,
    import_all,
    list_areas,
    log_entry,
    log_journal,
    log_screen_session,
    log_slip,
    log_update,
    seed_demo,
    update_task,
)
from atlas.settings import load_settings

app = typer.Typer(no_args_is_help=True, add_completion=False)
area_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define areas.")
metric_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define metrics.")
habit_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define habits.")
goal_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define goals.")
entry_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Amend or delete entries.")
task_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Capture one-off tasks.")
screen_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Log screen sessions.")

app.add_typer(area_app, name="area")
app.add_typer(metric_app, name="metric")
app.add_typer(habit_app, name="habit")
app.add_typer(goal_app, name="goal")
app.add_typer(entry_app, name="entry")
app.add_typer(task_app, name="task")
app.add_typer(screen_app, name="screen")


@app.callback()
def main() -> None:
    """Capture and admin CLI. Review lives in the web UI."""


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


@app.command()
def log(
    metric: Annotated[str, typer.Argument(help="Metric slug; unique prefixes match.")],
    value: Annotated[str | None, typer.Argument(help="Value to record.")] = None,
    on: Annotated[str | None, typer.Option("--on")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
) -> None:
    """Record an observation. The capture hot path."""
    with cli_session() as session:
        slug = resolve_metric_slug(session, metric)
        entry = log_entry(
            session,
            slug,
            parse_log_value(value),
            occurred_on=parse_iso_date(on),
            note=note,
        )
        print_logged(slug, entry)


@app.command("update")
def checkin(
    on: Annotated[str | None, typer.Option("--on")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
) -> None:
    """Record today's check-in (the Updates widget)."""
    with cli_session() as session:
        entry = log_update(session, occurred_on=parse_iso_date(on), note=note)
        print_logged("checkin", entry)


@app.command()
def slip(
    on: Annotated[str | None, typer.Option("--on")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
) -> None:
    """Record a slip (count of 1 on the well-known slip metric)."""
    with cli_session() as session:
        entry = log_slip(session, occurred_on=parse_iso_date(on), note=note)
        print_logged("slip", entry)


@app.command()
def journal(
    text: Annotated[str, typer.Argument()],
    on: Annotated[str | None, typer.Option("--on")] = None,
) -> None:
    """Record a journal entry on the well-known journal metric."""
    with cli_session() as session:
        entry = log_journal(session, text, occurred_on=parse_iso_date(on))
        print_logged("journal", entry)


@area_app.command("add")
def area_add(
    slug: Annotated[str, typer.Argument()],
    name: Annotated[str | None, typer.Option("--name")] = None,
    description: Annotated[str | None, typer.Option("--description")] = None,
) -> None:
    """Define an area."""
    with cli_session() as session:
        area = create_area(session, slug, name=name, description=description)
        print_created("area", area.slug)


@metric_app.command("add")
def metric_add(
    slug: Annotated[str, typer.Argument()],
    area: Annotated[str, typer.Option("--area")],
    value_type: Annotated[ValueType, typer.Option("--type")],
    aggregation: Annotated[Aggregation, typer.Option("--agg")],
    name: Annotated[str | None, typer.Option("--name")] = None,
    unit: Annotated[str | None, typer.Option("--unit")] = None,
    direction: Annotated[Direction, typer.Option("--direction")] = Direction.NEUTRAL,
) -> None:
    """Define a metric."""
    with cli_session() as session:
        metric = create_metric(
            session,
            slug,
            area_slug=area,
            value_type=value_type,
            aggregation=aggregation,
            name=name,
            unit=unit,
            direction=direction,
        )
        print_created("metric", metric.slug)


@habit_app.command("add")
def habit_add(
    metric: Annotated[str, typer.Option("--metric")],
    period: Annotated[Period, typer.Option("--period")],
    slug: Annotated[str | None, typer.Argument()] = None,
    at_least: Annotated[float | None, typer.Option("--at-least")] = None,
    at_most: Annotated[float | None, typer.Option("--at-most")] = None,
    exactly: Annotated[float | None, typer.Option("--exactly")] = None,
    name: Annotated[str | None, typer.Option("--name")] = None,
    weekdays: Annotated[str | None, typer.Option("--weekdays")] = None,
    active_from: Annotated[str | None, typer.Option("--from")] = None,
    active_to: Annotated[str | None, typer.Option("--to")] = None,
) -> None:
    """Define a habit over a metric."""
    with cli_session() as session:
        comparator, target_value = comparator_and_target(at_least, at_most, exactly)
        habit_slug = slug if slug is not None else f"{metric}-{period}"
        habit = create_habit(
            session,
            habit_slug,
            metric_slug=metric,
            period=period,
            target_value=target_value,
            comparator=comparator,
            name=name,
            weekdays=parse_weekdays(weekdays),
            active_from=parse_iso_date(active_from),
            active_to=parse_iso_date(active_to),
        )
        print_created("habit", habit.slug)


@goal_app.command("add")
def goal_add(
    name: Annotated[str, typer.Argument()],
    by: Annotated[str, typer.Option("--by")],
    slug: Annotated[str | None, typer.Option("--slug")] = None,
    area: Annotated[str | None, typer.Option("--area")] = None,
    kind: Annotated[GoalKind | None, typer.Option("--kind")] = None,
    metric: Annotated[str | None, typer.Option("--metric")] = None,
    target: Annotated[float | None, typer.Option("--target")] = None,
    at_least: Annotated[bool, typer.Option("--at-least")] = False,
    at_most: Annotated[bool, typer.Option("--at-most")] = False,
    exactly: Annotated[bool, typer.Option("--exactly")] = False,
    baseline: Annotated[float | None, typer.Option("--baseline")] = None,
    cumulative: Annotated[bool, typer.Option("--cumulative")] = False,
    start: Annotated[str | None, typer.Option("--start")] = None,
    horizon: Annotated[GoalHorizon | None, typer.Option("--horizon")] = None,
    parent: Annotated[str | None, typer.Option("--parent")] = None,
    description: Annotated[str | None, typer.Option("--description")] = None,
) -> None:
    """Define a goal."""
    with cli_session() as session:
        resolved_kind = kind or (
            GoalKind.METRIC_TARGET if metric is not None else GoalKind.MILESTONE
        )
        area_slug = area if area is not None else _area_slug_for_metric(session, metric)
        comparator = None
        measure = None
        if resolved_kind is GoalKind.METRIC_TARGET:
            comparator = comparator_from_flags(at_least, at_most, exactly)
            measure = measure_from_flag(cumulative)
        elif (
            metric is not None or at_least or at_most or exactly or cumulative or target is not None
        ):
            fail("milestone goals must not set --metric, --target, or a comparator")
        goal = create_goal(
            session,
            slug if slug is not None else slugify(name),
            area_slug=area_slug,
            kind=resolved_kind,
            start_on=parse_iso_date(start) or load_settings().today(),
            due_on=require_iso_date(by),
            name=name,
            metric_slug=metric,
            target_value=target,
            comparator=comparator,
            baseline_value=baseline,
            measure=measure,
            horizon=horizon,
            parent_slug=parent,
            description=description,
        )
        print_created("goal", goal.slug)


@entry_app.command("amend")
def entry_amend(
    entry_id: Annotated[int, typer.Argument(metavar="ID")],
    value: Annotated[str | None, typer.Option("--value")] = None,
    on: Annotated[str | None, typer.Option("--on")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
) -> None:
    """Correct an entry."""
    with cli_session() as session:
        updates: dict[str, object] = {}
        if value is not None:
            updates["value"] = parse_log_value(value)
        if on is not None:
            updates["occurred_on"] = parse_iso_date(on)
        if note is not None:
            updates["note"] = note
        if not updates:
            fail("nothing to amend; pass --value, --on, or --note")
        print_amended(amend_entry(session, entry_id, **updates))


@entry_app.command("rm")
def entry_rm(entry_id: Annotated[int, typer.Argument(metavar="ID")]) -> None:
    """Delete an entry."""
    with cli_session() as session:
        delete_entry(session, entry_id)
        print_deleted(entry_id)


@task_app.command("add")
def task_add(
    title: Annotated[str, typer.Argument()],
    bucket: Annotated[TaskBucket, typer.Option("--bucket")] = TaskBucket.TODAY,
    priority: Annotated[TaskPriority, typer.Option("--priority")] = TaskPriority.NORMAL,
    due: Annotated[str | None, typer.Option("--due")] = None,
    goal: Annotated[str | None, typer.Option("--goal")] = None,
) -> None:
    """Add a one-off task."""
    with cli_session() as session:
        task = create_task(
            session,
            title,
            bucket=bucket,
            due_on=parse_iso_date(due),
            priority=priority,
            goal_slug=goal,
        )
        typer.echo(f"created task #{task.id} {task.title}")


@task_app.command("done")
def task_done(task_id: Annotated[int, typer.Argument(metavar="ID")]) -> None:
    """Mark a task complete."""
    with cli_session() as session:
        task = update_task(session, task_id, done=True)
        typer.echo(f"done task #{task.id} {task.title}")


@screen_app.command("log")
def screen_log(
    app_slug: Annotated[str, typer.Argument(metavar="APP")],
    minutes: Annotated[float | None, typer.Argument()] = None,
    started: Annotated[str | None, typer.Option("--from")] = None,
    ended: Annotated[str | None, typer.Option("--to")] = None,
    device: Annotated[str | None, typer.Option("--device")] = None,
    on: Annotated[str | None, typer.Option("--on")] = None,
    note: Annotated[str | None, typer.Option("--note")] = None,
) -> None:
    """Record a screen session as an interval or a duration."""
    with cli_session() as session:
        row = log_screen_session(
            session,
            app_slug,
            minutes=minutes,
            started_at=parse_iso_datetime(started),
            ended_at=parse_iso_datetime(ended),
            occurred_on=parse_iso_date(on),
            device_slug=device,
            note=note,
        )
        print_screen_logged(app_slug, row)


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


def _area_slug_for_metric(session: Session, metric_slug: str | None) -> str | None:
    if metric_slug is None:
        return None
    metric = get_metric(session, metric_slug)
    for area in list_areas(session, include_archived=True):
        if area.id == metric.area_id:
            return area.slug
    fail(f"area for metric {metric_slug!r} not found")
