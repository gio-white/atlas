from typing import Any

from rich.console import Console
from rich.table import Table

from atlas.domain import Comparator
from atlas.services import (
    AreaView,
    GoalProgressReport,
    HabitStatus,
    TodayView,
    WeekView,
)

console = Console(highlight=False, width=120)

_COMPARATOR = {
    Comparator.AT_LEAST: "≥",
    Comparator.AT_MOST: "≤",
    Comparator.EXACTLY: "=",
}


def print_logged(metric_slug: str, entry: Any) -> None:
    value = format_entry_value(entry.value_num, entry.value_bool, entry.value_text)
    note = f"  {entry.note}" if entry.note else ""
    console.print(
        f"logged [bold]{metric_slug}[/bold] {value} on {entry.occurred_on} (#{entry.id}){note}"
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


def print_today(view: TodayView) -> None:
    console.print(f"[bold]Today[/bold] {view.as_of}")
    _print_habit_status_table(view.habits, empty="No habits due.")
    table = Table(title="Logged", show_lines=False)
    table.add_column("ID", justify="right")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_column("Note")
    if view.entries:
        for entry in view.entries:
            table.add_row(
                str(entry.id),
                entry.metric_slug,
                format_entry_value(entry.value_num, entry.value_bool, entry.value_text),
                entry.note or "",
            )
        console.print(table)
    else:
        console.print("No entries logged.")
    _print_goal_table(view.goals, empty="No active goals.")


def print_week(view: WeekView) -> None:
    console.print(f"[bold]Week[/bold] {view.week_start} → {view.week_end}")
    if not view.habits:
        console.print("No habits this week.")
        return
    table = Table(show_lines=False)
    table.add_column("Habit", no_wrap=True)
    for cell in view.habits[0].days:
        table.add_column(f"{cell.day:%a} {cell.day.day}", justify="center")
    table.add_column("Streak", justify="right")
    for habit in view.habits:
        row = [habit.slug]
        for cell in habit.days:
            if not cell.scheduled:
                row.append("")
            elif cell.value is None:
                row.append("·")
            else:
                row.append(format_number(cell.value))
        row.append(str(habit.current_streak))
        table.add_row(*row)
    console.print(table)


def print_area(view: AreaView) -> None:
    console.print(f"[bold]{view.name}[/bold] ({view.slug})  {view.as_of}")
    if view.description:
        console.print(view.description)
    table = Table(title="Metrics", show_lines=False)
    table.add_column("Metric")
    table.add_column("Latest")
    table.add_column("On")
    table.add_column("Unit")
    if view.metrics:
        for metric in view.metrics:
            table.add_row(
                metric.slug,
                format_number(metric.latest_value),
                str(metric.latest_on) if metric.latest_on is not None else "—",
                metric.unit or "",
            )
        console.print(table)
    else:
        console.print("No metrics.")
    _print_habit_status_table(view.habits, empty="No habits.")
    _print_goal_table(view.goals, empty="No goals.")


def print_habit_status(status: HabitStatus) -> None:
    target = format_target(status.comparator, status.target_value)
    mark = "✓" if status.satisfied else "·"
    console.print(f"[bold]{status.name}[/bold] ({status.slug})")
    console.print(f"  metric    {status.metric_slug}  {status.period}  {target}")
    console.print(f"  streak    {status.current_streak}  (longest {status.longest_streak})")
    console.print(f"  adhere    {format_pct(status.adherence)}")
    console.print(f"  current   {format_number(status.current_value)}  {mark}")


def print_goals(reports: list[GoalProgressReport]) -> None:
    _print_goal_table(reports, empty="No goals.")


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


def format_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{round(value * 100)}%"


def format_target(comparator: Comparator, target_value: float) -> str:
    return f"{_COMPARATOR[Comparator(comparator)]} {format_number(target_value)}"


def _print_habit_status_table(habits: list[HabitStatus], *, empty: str) -> None:
    table = Table(title="Habits", show_lines=False)
    table.add_column("Habit")
    table.add_column("Value", justify="right")
    table.add_column("Target")
    table.add_column("Streak", justify="right")
    table.add_column("")
    if not habits:
        console.print(empty)
        return
    for habit in habits:
        mark = "✓" if habit.satisfied else "·"
        table.add_row(
            habit.slug,
            format_number(habit.current_value),
            format_target(habit.comparator, habit.target_value),
            str(habit.current_streak),
            mark,
        )
    console.print(table)


def _print_goal_table(reports: list[GoalProgressReport], *, empty: str) -> None:
    table = Table(title="Goals", show_lines=False)
    table.add_column("Goal")
    table.add_column("Progress")
    table.add_column("Pace")
    table.add_column("Due")
    table.add_column("Status")
    if not reports:
        console.print(empty)
        return
    for report in reports:
        table.add_row(
            report.slug,
            format_pct(report.fraction),
            str(report.pace),
            str(report.due_on),
            str(report.status),
        )
    console.print(table)
