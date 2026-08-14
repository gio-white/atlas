from typing import Any

from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table

from atlas.domain import Comparator, Period
from atlas.services import (
    AreaView,
    GoalProgressReport,
    HabitStatus,
    LoggedEntry,
    MetricSnapshot,
    SeedSummary,
    TodayView,
    WeekView,
)

console = Console(highlight=False)

_TWO_PANE_MIN_WIDTH = 100

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


def print_seeded(summary: SeedSummary) -> None:
    console.print(
        f"seeded demo as of {summary.as_of}: "
        f"{summary.areas} areas, {summary.metrics} metrics, "
        f"{summary.habits} habits, {summary.goals} goals, "
        f"{summary.entries} entries"
    )


def print_today(view: TodayView) -> None:
    _header("Today", str(view.as_of))
    daily = [habit for habit in view.habits if habit.period is Period.DAY]
    period = [habit for habit in view.habits if habit.period is not Period.DAY]
    console.print(
        _two_pane(
            _section("Daily", _habit_status_table(daily), "No daily habits due."),
            _section(
                "This period",
                _habit_status_table(period),
                "No weekly or monthly habits due.",
            ),
        )
    )
    console.print(_section("Logged", _logged_table(view.entries), "No entries logged."))
    console.print(_section("Goals", _goal_table(view.goals), "No active goals."))


def print_week(view: WeekView) -> None:
    _header("Week", f"{view.week_start} → {view.week_end}")
    console.print(_section("Habits", _week_grid(view), "No habits this week."))


def print_area(view: AreaView) -> None:
    _header(view.name, f"({view.slug})  {view.as_of}")
    if view.description:
        console.print(view.description)
    daily = [habit for habit in view.habits if habit.period is Period.DAY]
    period = [habit for habit in view.habits if habit.period is not Period.DAY]
    console.print(_section("Metrics", _metrics_table(view.metrics), "No metrics."))
    console.print(
        _two_pane(
            _section("Daily", _habit_status_table(daily), "No daily habits."),
            _section(
                "This period",
                _habit_status_table(period),
                "No weekly or monthly habits.",
            ),
        )
    )
    console.print(_section("Goals", _goal_table(view.goals), "No goals."))


def print_habit_status(status: HabitStatus) -> None:
    _header(status.name, f"({status.slug})")
    target = format_target(status.comparator, status.target_value)
    mark = "✓" if status.satisfied else "·"
    table = Table(box=None, pad_edge=False, show_header=False)
    table.add_column(no_wrap=True)
    table.add_column()
    table.add_row("metric", f"{status.metric_slug}  {status.period}  {target}")
    table.add_row("streak", f"{status.current_streak}  (longest {status.longest_streak})")
    table.add_row("adhere", format_pct(status.adherence))
    table.add_row("current", f"{format_number(status.current_value)}  {mark}")
    console.print(_section("Status", table, ""))


def print_goals(reports: list[GoalProgressReport]) -> None:
    console.print(_section("Goals", _goal_table(reports), "No goals."))


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


def _header(title: str, detail: str = "") -> None:
    if detail:
        console.print(f"[bold]{title}[/bold] {detail}")
    else:
        console.print(f"[bold]{title}[/bold]")


def _section(title: str, body: RenderableType | None, empty: str) -> Panel:
    return Panel(
        body if body is not None else empty,
        title=title,
        title_align="left",
        padding=(0, 1),
    )


def _two_pane(left: RenderableType, right: RenderableType) -> RenderableType:
    if console.size.width < _TWO_PANE_MIN_WIDTH:
        return Group(left, right)
    row = Table.grid(expand=True, padding=0)
    row.add_column(ratio=1)
    row.add_column(ratio=1)
    row.add_row(left, right)
    return row


def _habit_status_table(habits: list[HabitStatus]) -> Table | None:
    if not habits:
        return None
    table = Table(box=None, pad_edge=False, expand=False)
    table.add_column("", min_width=2, no_wrap=True)
    table.add_column("Habit", no_wrap=True)
    table.add_column("Value", justify="right", no_wrap=True)
    table.add_column("Target", no_wrap=True)
    table.add_column("Streak", justify="right", no_wrap=True)
    for habit in habits:
        table.add_row(
            "✓" if habit.satisfied else "·",
            habit.slug,
            format_number(habit.current_value),
            format_target(habit.comparator, habit.target_value),
            str(habit.current_streak),
        )
    return table


def _logged_table(entries: list[LoggedEntry]) -> Table | None:
    if not entries:
        return None
    table = Table(box=None, pad_edge=False, expand=True)
    table.add_column("ID", justify="right", no_wrap=True)
    table.add_column("Metric")
    table.add_column("Value")
    table.add_column("Note")
    for entry in entries:
        table.add_row(
            str(entry.id),
            entry.metric_slug,
            format_entry_value(entry.value_num, entry.value_bool, entry.value_text),
            entry.note or "",
        )
    return table


def _goal_table(reports: list[GoalProgressReport]) -> Table | None:
    if not reports:
        return None
    table = Table(box=None, pad_edge=False, expand=True)
    table.add_column("Goal")
    table.add_column("Horizon", no_wrap=True)
    table.add_column("Progress", no_wrap=True)
    table.add_column("Pace", no_wrap=True)
    table.add_column("Due", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    for report in reports:
        table.add_row(
            report.slug,
            str(report.horizon),
            format_pct(report.fraction),
            str(report.pace),
            str(report.due_on),
            str(report.status),
        )
    return table


def _metrics_table(metrics: list[MetricSnapshot]) -> Table | None:
    if not metrics:
        return None
    table = Table(box=None, pad_edge=False, expand=True)
    table.add_column("Metric")
    table.add_column("Latest")
    table.add_column("On")
    table.add_column("Unit")
    for metric in metrics:
        table.add_row(
            metric.slug,
            format_number(metric.latest_value),
            str(metric.latest_on) if metric.latest_on is not None else "—",
            metric.unit or "",
        )
    return table


def _week_grid(view: WeekView) -> Table | None:
    if not view.habits:
        return None
    table = Table(box=None, pad_edge=False, expand=True)
    table.add_column("Habit", no_wrap=True)
    for cell in view.habits[0].days:
        table.add_column(f"{cell.day:%a} {cell.day.day}", justify="center", no_wrap=True)
    table.add_column("Streak", justify="right", no_wrap=True)
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
    return table
