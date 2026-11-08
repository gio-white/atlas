"""Read models for the quest screens: Main quests, Ambition, Goal, Side quests, Side quest,
Inbox, Today, and Calendar. Every number comes from `atlas.domain.quests` via `QuestIndex`."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlmodel import Session

from atlas.domain import QuestStatus, TaskStatus, TimeBlockStatus
from atlas.domain.quests import QuestKind, as_utc, is_unconfirmed, overlapping_ids
from atlas.services.clock import resolve_today
from atlas.services.quests import (
    BlockItem,
    ContainerView,
    ItemRef,
    QuestIndex,
    TaskView,
    block_item,
    block_view,
)
from atlas.settings import load_settings


@dataclass(frozen=True, slots=True)
class ChapterTree:
    chapter: ContainerView
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class MilestoneTree:
    milestone: ContainerView
    chapters: list[ChapterTree]
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class AmbitionSection:
    ambition: ContainerView
    goals: list[ContainerView]
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class MainQuestsView:
    ambitions: list[AmbitionSection]
    independent_goals: list[ContainerView]


@dataclass(frozen=True, slots=True)
class GoalTree:
    goal: ContainerView
    milestones: list[MilestoneTree]
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class SideQuestTree:
    side_quest: ContainerView
    chapters: list[ChapterTree]
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class SideQuestsView:
    side_quests: list[ContainerView]
    standalone_tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class InboxView:
    count: int
    tasks: list[TaskView]


@dataclass(frozen=True, slots=True)
class ScheduledBlock:
    block: BlockItem
    task: TaskView


@dataclass(frozen=True, slots=True)
class TodayView:
    date: date
    blocks: list[ScheduledBlock]
    unconfirmed: list[ScheduledBlock]
    due_today: list[TaskView]
    up_next: list[TaskView]


@dataclass(frozen=True, slots=True)
class CalendarView:
    start: datetime
    end: datetime
    blocks: list[ScheduledBlock]


def main_quests_view(
    session: Session, *, include_archived: bool = False, now: datetime | None = None
) -> MainQuestsView:
    now = _now(now)
    index = QuestIndex(session)
    ambitions = [
        _ambition_section(index, ambition_id, now, include_archived)
        for ambition_id in _roots(index, QuestKind.AMBITION, include_archived)
    ]
    goals = [
        index.container_view(QuestKind.GOAL, goal_id, now)
        for goal_id in _roots(index, QuestKind.GOAL, include_archived)
    ]
    return MainQuestsView(ambitions=ambitions, independent_goals=goals)


def ambition_view(
    session: Session,
    ambition_id: int,
    *,
    include_archived: bool = False,
    now: datetime | None = None,
) -> AmbitionSection:
    return _ambition_section(QuestIndex(session), ambition_id, _now(now), include_archived)


def goal_view(
    session: Session, goal_id: int, *, include_archived: bool = False, now: datetime | None = None
) -> GoalTree:
    now = _now(now)
    index = QuestIndex(session)
    goal = index.container_view(QuestKind.GOAL, goal_id, now)
    milestones = [
        MilestoneTree(
            milestone=index.container_view(QuestKind.MILESTONE, milestone_id, now),
            chapters=_chapters(index, QuestKind.MILESTONE, milestone_id, now, include_archived),
            tasks=_tasks(index, QuestKind.MILESTONE, milestone_id, now, include_archived),
        )
        for milestone_id in _children(
            index, QuestKind.GOAL, goal_id, QuestKind.MILESTONE, include_archived
        )
    ]
    tasks = _tasks(index, QuestKind.GOAL, goal_id, now, include_archived)
    return GoalTree(goal=goal, milestones=milestones, tasks=tasks)


def side_quests_view(
    session: Session, *, include_archived: bool = False, now: datetime | None = None
) -> SideQuestsView:
    now = _now(now)
    index = QuestIndex(session)
    side_quests = [
        index.container_view(QuestKind.SIDE_QUEST, side_id, now)
        for side_id in _roots(index, QuestKind.SIDE_QUEST, include_archived)
    ]
    standalone = [
        index.task_view(row.id, now)
        for row in _sorted(index.rows[QuestKind.TASK].values())
        if _is_loose(index, row)
        and row.organized_at is not None
        and (include_archived or row.archived_at is None)
    ]
    return SideQuestsView(side_quests=side_quests, standalone_tasks=standalone)


def side_quest_view(
    session: Session,
    side_quest_id: int,
    *,
    include_archived: bool = False,
    now: datetime | None = None,
) -> SideQuestTree:
    now = _now(now)
    index = QuestIndex(session)
    return SideQuestTree(
        side_quest=index.container_view(QuestKind.SIDE_QUEST, side_quest_id, now),
        chapters=_chapters(index, QuestKind.SIDE_QUEST, side_quest_id, now, include_archived),
        tasks=_tasks(index, QuestKind.SIDE_QUEST, side_quest_id, now, include_archived),
    )


def inbox_view(session: Session, *, now: datetime | None = None) -> InboxView:
    """Inbox tasks (no parent, never organized, not archived), newest first."""
    now = _now(now)
    index = QuestIndex(session)
    rows = [
        row
        for row in index.rows[QuestKind.TASK].values()
        if _is_loose(index, row) and row.organized_at is None and row.archived_at is None
    ]
    rows.sort(key=lambda row: (as_utc(row.created_at), row.id), reverse=True)
    return InboxView(count=len(rows), tasks=[index.task_view(row.id, now) for row in rows])


def today_view(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> TodayView:
    """Today's non-cancelled blocks (local day in ATLAS_TZ), every unconfirmed block, open tasks
    due today or earlier, and the next action of each active goal and side quest."""
    now = _now(now)
    day = resolve_today(as_of)
    start, end = local_day_bounds(day)
    index = QuestIndex(session)
    blocks: list[ScheduledBlock] = []
    unconfirmed: list[ScheduledBlock] = []
    for rows in index.blocks.values():
        for row in rows:
            view = block_view(row)
            task_open = index.rows[QuestKind.TASK][row.task_id].archived_at is None
            if is_unconfirmed(view, now) and task_open:
                unconfirmed.append(_scheduled(index, row, now))
            if (
                view.status is not TimeBlockStatus.CANCELLED
                and view.start_at < end
                and view.end_at > start
            ):
                blocks.append(_scheduled(index, row, now))
    blocks.sort(key=lambda item: (item.block.start_at, item.block.id))
    unconfirmed.sort(key=lambda item: (item.block.start_at, item.block.id))
    due = [
        row
        for row in index.rows[QuestKind.TASK].values()
        if row.due_on is not None
        and row.due_on <= day
        and TaskStatus(row.status) is not TaskStatus.COMPLETED
        and row.archived_at is None
    ]
    due.sort(key=lambda row: (row.due_on, row.position, row.id))
    scheduled_today = {item.task.id for item in blocks}
    up_next: list[TaskView] = []
    seen: set[int] = set()
    for kind in (QuestKind.GOAL, QuestKind.SIDE_QUEST):
        for row in _sorted(index.rows[kind].values()):
            if QuestStatus(row.status) is not QuestStatus.ACTIVE:
                continue
            action = index.container_view(kind, row.id, now).next_action
            if action is None or action.id in seen or action.id in scheduled_today:
                continue
            seen.add(action.id)
            up_next.append(action)
    return TodayView(
        date=day,
        blocks=blocks,
        unconfirmed=unconfirmed,
        due_today=[index.task_view(row.id, now) for row in due],
        up_next=up_next,
    )


def calendar_view(
    session: Session, *, start: datetime, end: datetime, now: datetime | None = None
) -> CalendarView:
    """Every block overlapping [start, end) with its task and parent path; overlaps marked."""
    now = _now(now)
    start, end = as_utc(start), as_utc(end)
    index = QuestIndex(session)
    rows = [
        row
        for rows in index.blocks.values()
        for row in rows
        if as_utc(row.start_at) < end and as_utc(row.end_at) > start
    ]
    rows.sort(key=lambda row: (as_utc(row.start_at), row.id))
    overlaps = overlapping_ids([block_view(row) for row in rows])
    return CalendarView(
        start=start,
        end=end,
        blocks=[_scheduled(index, row, now, overlaps=row.id in overlaps) for row in rows],
    )


def local_day_bounds(day: date) -> tuple[datetime, datetime]:
    zone = load_settings().timezone
    start = datetime.combine(day, time.min, tzinfo=zone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)


def _ambition_section(
    index: QuestIndex, ambition_id: int, now: datetime, include_archived: bool
) -> AmbitionSection:
    return AmbitionSection(
        ambition=index.container_view(QuestKind.AMBITION, ambition_id, now),
        goals=[
            index.container_view(QuestKind.GOAL, goal_id, now)
            for goal_id in _children(
                index, QuestKind.AMBITION, ambition_id, QuestKind.GOAL, include_archived
            )
        ],
        tasks=_tasks(index, QuestKind.AMBITION, ambition_id, now, include_archived),
    )


def _chapters(
    index: QuestIndex, kind: QuestKind, item_id: int, now: datetime, include_archived: bool
) -> list[ChapterTree]:
    return [
        ChapterTree(
            chapter=index.container_view(QuestKind.CHAPTER, chapter_id, now),
            tasks=_tasks(index, QuestKind.CHAPTER, chapter_id, now, include_archived),
        )
        for chapter_id in _children(index, kind, item_id, QuestKind.CHAPTER, include_archived)
    ]


def _tasks(
    index: QuestIndex, kind: QuestKind, item_id: int, now: datetime, include_archived: bool
) -> list[TaskView]:
    return [
        index.task_view(task_id, now)
        for task_id in _children(index, kind, item_id, QuestKind.TASK, include_archived)
    ]


def _children(
    index: QuestIndex,
    kind: QuestKind,
    item_id: int,
    child_kind: QuestKind,
    include_archived: bool,
) -> list[int]:
    ids = index.ordered_children(kind, item_id, child_kind)
    if include_archived:
        return ids
    return [child_id for child_id in ids if index.row(child_kind, child_id).archived_at is None]


def _roots(index: QuestIndex, kind: QuestKind, include_archived: bool) -> list[int]:
    rows = index.rows[kind].values()
    if kind is QuestKind.GOAL:
        rows = [row for row in rows if row.ambition_id is None]
    return [row.id for row in _sorted(rows) if include_archived or row.archived_at is None]


def _is_loose(index: QuestIndex, row) -> bool:
    return not any(
        getattr(row, column) is not None
        for column in ("ambition_id", "goal_id", "milestone_id", "chapter_id", "side_quest_id")
    )


def _sorted(rows):
    return sorted(rows, key=lambda row: (row.position, row.id))


def _scheduled(index: QuestIndex, row, now: datetime, *, overlaps: bool = False) -> ScheduledBlock:
    return ScheduledBlock(
        block=block_item(row, now, overlaps=overlaps), task=index.task_view(row.task_id, now)
    )


def _now(now: datetime | None) -> datetime:
    return as_utc(now) if now is not None else datetime.now(UTC)


__all__ = [
    "AmbitionSection",
    "CalendarView",
    "ChapterTree",
    "GoalTree",
    "InboxView",
    "ItemRef",
    "MainQuestsView",
    "MilestoneTree",
    "ScheduledBlock",
    "SideQuestTree",
    "SideQuestsView",
    "TodayView",
    "ambition_view",
    "calendar_view",
    "goal_view",
    "inbox_view",
    "main_quests_view",
    "side_quest_view",
    "side_quests_view",
    "today_view",
]
