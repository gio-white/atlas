from rich.console import Console

from atlas.services import SeedSummary

console = Console(highlight=False)


def print_imported(path: str, *, replace: bool, notes: list[str] | None = None) -> None:
    mode = "replaced and imported" if replace else "imported"
    console.print(f"{mode} {path}")
    for note in notes or []:
        console.print(note)


def print_seeded(summary: SeedSummary) -> None:
    console.print(
        f"seeded demo as of {summary.as_of}: "
        f"{summary.areas} areas, {summary.metrics} metrics, "
        f"{summary.habits} habits, {summary.entries} entries, "
        f"{summary.screen_categories} screen categories, "
        f"{summary.screen_apps} screen apps, "
        f"{summary.screen_devices} screen devices, "
        f"{summary.screen_sessions} screen sessions, "
        f"{summary.entertainment_topics} entertainment topics, "
        f"{summary.entertainment_titles} entertainment titles, "
        f"{summary.sleep_sessions} sleep sessions, "
        f"{summary.ambitions} ambitions, {summary.goals} goals, "
        f"{summary.milestones} milestones, {summary.side_quests} side quests, "
        f"{summary.chapters} chapters, {summary.tasks} tasks, "
        f"{summary.time_blocks} time blocks"
    )
