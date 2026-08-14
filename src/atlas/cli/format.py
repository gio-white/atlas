from typing import Any

from rich.console import Console

from atlas.services import SeedSummary

console = Console(highlight=False)


def print_logged(metric_slug: str, entry: Any) -> None:
    value = format_entry_value(entry.value_num, entry.value_bool, entry.value_text)
    note = f"  {entry.note}" if entry.note else ""
    console.print(
        f"logged [bold]{metric_slug}[/bold] {value} on {entry.occurred_on} (#{entry.id}){note}"
    )


def print_screen_logged(app_slug: str, row: Any) -> None:
    extra = ""
    if row.started_at is not None and row.ended_at is not None:
        extra = f"  {row.started_at.isoformat()}–{row.ended_at.isoformat()}"
    note = f"  {row.note}" if row.note else ""
    console.print(
        f"logged [bold]{app_slug}[/bold] {row.minutes}m on {row.occurred_on} (#{row.id})"
        f"{extra}{note}"
    )


def print_created(kind: str, slug: str) -> None:
    console.print(f"created {kind} [bold]{slug}[/bold]")


def print_amended(entry: Any) -> None:
    value = format_entry_value(entry.value_num, entry.value_bool, entry.value_text)
    console.print(f"amended entry #{entry.id}  {value} on {entry.occurred_on}")


def print_deleted(entry_id: int) -> None:
    console.print(f"deleted entry #{entry_id}")


def print_imported(path: str, *, replace: bool) -> None:
    mode = "replaced and imported" if replace else "imported"
    console.print(f"{mode} {path}")


def print_seeded(summary: SeedSummary) -> None:
    console.print(
        f"seeded demo as of {summary.as_of}: "
        f"{summary.areas} areas, {summary.metrics} metrics, "
        f"{summary.habits} habits, {summary.goals} goals, "
        f"{summary.entries} entries"
    )


def format_entry_value(
    value_num: float | None, value_bool: bool | None, value_text: str | None
) -> str:
    if value_num is not None:
        return format_number(value_num)
    if value_bool is not None:
        return "yes" if value_bool else "no"
    if value_text is not None:
        return value_text
    return "—"


def format_number(value: float | None) -> str:
    if value is None:
        return "—"
    if value == int(value):
        return str(int(value))
    return f"{value:g}"
