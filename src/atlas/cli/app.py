import json
from pathlib import Path
from typing import Annotated

import typer
from sqlmodel import Session

from atlas.cli.format import (
    print_amended,
    print_area,
    print_created,
    print_deleted,
    print_goals,
    print_habit_status,
    print_imported,
    print_logged,
    print_seeded,
    print_today,
    print_week,
)
from atlas.cli.group import FallbackToShowGroup
from atlas.cli.lookup import resolve_metric_slug
from atlas.cli.parse import (
    comparator_and_target,
    comparator_from_flags,
    measure_from_flag,
    parse_iso_date,
    parse_log_value,
    parse_weekdays,
    require_iso_date,
    slugify,
)
from atlas.cli.session import cli_session, fail
from atlas.db import init_db
from atlas.domain import Aggregation, Direction, GoalKind, GoalStatus, Period, ValueType
from atlas.services import (
    amend_entry,
    area_view,
    create_area,
    create_goal,
    create_habit,
    create_metric,
    delete_entry,
    export_all,
    get_metric,
    goal_progress,
    habit_status,
    import_all,
    list_areas,
    list_goals,
    log_entry,
    seed_demo,
    today_view,
    week_view,
)
from atlas.settings import load_settings

app = typer.Typer(no_args_is_help=True, add_completion=False)
area_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    cls=FallbackToShowGroup,
    help="Define and review areas.",
)
metric_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define metrics.")
habit_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    cls=FallbackToShowGroup,
    help="Define and review habits.",
)
goal_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Define goals.")
entry_app = typer.Typer(no_args_is_help=True, add_completion=False, help="Amend or delete entries.")

app.add_typer(area_app, name="area")
app.add_typer(metric_app, name="metric")
app.add_typer(habit_app, name="habit")
app.add_typer(goal_app, name="goal")
app.add_typer(entry_app, name="entry")


@app.callback()
def main() -> None:
    """Personal life-tracking CLI."""


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


@area_app.command("show")
def area_show(
    slug: Annotated[str, typer.Argument()],
    on: Annotated[str | None, typer.Option("--on")] = None,
) -> None:
    """Review one area's metrics, habits, and goals."""
    with cli_session() as session:
        print_area(area_view(session, slug, as_of=parse_iso_date(on)))


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


@habit_app.command("show")
def habit_show(
    slug: Annotated[str, typer.Argument()],
    on: Annotated[str | None, typer.Option("--on")] = None,
) -> None:
    """Review one habit's streak and adherence."""
    with cli_session() as session:
        print_habit_status(habit_status(session, slug, as_of=parse_iso_date(on)))


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
            metric is not None
            or at_least
            or at_most
            or exactly
            or cumulative
            or target is not None
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
        )
        print_created("goal", goal.slug)


@app.command()
def goals(
    area: Annotated[str | None, typer.Option("--area")] = None,
    status: Annotated[GoalStatus | None, typer.Option("--status")] = None,
    on: Annotated[str | None, typer.Option("--on")] = None,
) -> None:
    """Review goals with progress and pace."""
    with cli_session() as session:
        as_of = parse_iso_date(on)
        reports = [
            goal_progress(session, goal.slug, as_of=as_of)
            for goal in list_goals(session, area_slug=area, status=status)
        ]
        print_goals(reports)


@app.command()
def today(on: Annotated[str | None, typer.Option("--on")] = None) -> None:
    """What is due today and what is logged."""
    with cli_session() as session:
        print_today(today_view(session, as_of=parse_iso_date(on)))


@app.command()
def week(on: Annotated[str | None, typer.Option("--on")] = None) -> None:
    """The current week across habits."""
    with cli_session() as session:
        print_week(week_view(session, as_of=parse_iso_date(on)))


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


def _area_slug_for_metric(session: Session, metric_slug: str | None) -> str:
    if metric_slug is None:
        fail("provide --area, or --metric so the area can be inferred")
    metric = get_metric(session, metric_slug)
    for area in list_areas(session, include_archived=True):
        if area.id == metric.area_id:
            return area.slug
    fail(f"area for metric {metric_slug!r} not found")
