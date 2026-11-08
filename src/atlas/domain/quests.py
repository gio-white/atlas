"""Quest rules: structure, task status, chapter state, completion, progress, next action, and
time blocks. Pure functions over in-memory values; the services build the trees from rows.

Definitions are in docs/domain/quests.md and docs/domain/time-blocks.md.
"""

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum

from atlas.domain.enums import (
    ChapterState,
    ParentKind,
    TaskPriority,
    TaskStatus,
    TimeBlockStatus,
)


class QuestKind(StrEnum):
    AMBITION = "ambition"
    GOAL = "goal"
    MILESTONE = "milestone"
    SIDE_QUEST = "side_quest"
    CHAPTER = "chapter"
    TASK = "task"


class QuestRuleError(ValueError):
    """A quest rule was broken (invalid parent, archived parent, completed task, ...)."""


class NeedsOverrideError(QuestRuleError):
    """Completing an item that is not eligible without `override`."""


# --- Structure (plan §4.1) -------------------------------------------------------------------

ALLOWED_PARENTS: dict[QuestKind, frozenset[ParentKind]] = {
    QuestKind.AMBITION: frozenset(),
    QuestKind.GOAL: frozenset({ParentKind.AMBITION}),
    QuestKind.MILESTONE: frozenset({ParentKind.GOAL}),
    QuestKind.SIDE_QUEST: frozenset(),
    QuestKind.CHAPTER: frozenset({ParentKind.MILESTONE, ParentKind.SIDE_QUEST}),
    QuestKind.TASK: frozenset(
        {
            ParentKind.AMBITION,
            ParentKind.GOAL,
            ParentKind.MILESTONE,
            ParentKind.CHAPTER,
            ParentKind.SIDE_QUEST,
        }
    ),
}

PARENT_REQUIRED: frozenset[QuestKind] = frozenset({QuestKind.MILESTONE, QuestKind.CHAPTER})


@dataclass(frozen=True, slots=True)
class ParentRef:
    kind: ParentKind
    id: int
    archived: bool = False


def check_parent(child: QuestKind, parent: ParentRef | None) -> None:
    """Raise `QuestRuleError` unless `parent` may hold a new or moved `child`."""
    if parent is None:
        if child in PARENT_REQUIRED:
            raise QuestRuleError(f"a {_label(child)} needs a parent")
        return
    if parent.kind not in ALLOWED_PARENTS[child]:
        raise QuestRuleError(f"a {_label(child)} cannot belong to a {_label(parent.kind)}")
    if parent.archived:
        raise QuestRuleError(f"{_label(parent.kind)} {parent.id} is archived")


# --- Task status (plan §4.2) -----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TaskTimes:
    status: TaskStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None


def transition_task(current: TaskTimes, status: TaskStatus, now: datetime) -> TaskTimes:
    """Move a task to `status`. Any status may go to any other (reopen included).

    `started_at` is stamped the first time the task leaves `todo` and never cleared;
    `completed_at` is set on completion (kept if already completed) and cleared otherwise.
    """
    started_at = current.started_at
    if started_at is None and status is not TaskStatus.TODO:
        started_at = now
    if status is TaskStatus.COMPLETED:
        completed_at = current.completed_at if current.completed_at is not None else now
    else:
        completed_at = None
    return TaskTimes(status=status, started_at=started_at, completed_at=completed_at)


# --- Tree values -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BlockView:
    id: int
    task_id: int
    start_at: datetime
    end_at: datetime
    status: TimeBlockStatus

    @property
    def minutes(self) -> float:
        return block_minutes(self)


@dataclass(frozen=True, slots=True)
class QuestNode:
    """One quest item with its non-archived and archived children.

    For a task `completed` mirrors `status`; for a container it is the stored status. Chapters
    have no stored completion, so their `completed` is always False and their state is computed.
    """

    kind: QuestKind
    id: int
    title: str = ""
    weight: float | None = None
    position: int = 0
    completed: bool = False
    archived: bool = False
    children: tuple["QuestNode", ...] = ()
    status: TaskStatus | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    due_on: date | None = None
    blocks: tuple[BlockView, ...] = field(default=())

    @property
    def is_task(self) -> bool:
        return self.kind is QuestKind.TASK

    def live_children(self) -> list["QuestNode"]:
        return [child for child in self.children if not child.archived]


def tree_order(children: Iterable[QuestNode]) -> list[QuestNode]:
    """Containers first, then direct tasks; each group by (position, id)."""
    return sorted(children, key=lambda node: (node.is_task, node.position, node.id))


def walk_tasks(node: QuestNode) -> Iterator[QuestNode]:
    """Non-archived tasks under `node` in tree order, skipping archived containers."""
    if node.is_task:
        if not node.archived:
            yield node
        return
    for child in tree_order(node.live_children()):
        yield from walk_tasks(child)


# --- Chapter state (plan §4.3) ---------------------------------------------------------------


def chapter_state(task_statuses: Sequence[TaskStatus]) -> ChapterState:
    """State of a chapter from its non-archived tasks. An empty chapter is never completed."""
    if not task_statuses:
        return ChapterState.EMPTY
    if all(status is TaskStatus.COMPLETED for status in task_statuses):
        return ChapterState.COMPLETED
    if any(status is not TaskStatus.TODO for status in task_statuses):
        return ChapterState.IN_PROGRESS
    return ChapterState.NOT_STARTED


def node_chapter_state(node: QuestNode) -> ChapterState:
    return chapter_state([child.status or TaskStatus.TODO for child in node.live_children()])


def is_done(node: QuestNode) -> bool:
    """Whether a child counts as finished for its parent's completion eligibility."""
    if node.kind is QuestKind.CHAPTER:
        return node_chapter_state(node) is ChapterState.COMPLETED
    return node.completed


# --- Completion eligibility (plan §4.4) ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CompletionCheck:
    eligible: bool
    open_children: tuple[QuestNode, ...]


def completion_check(node: QuestNode) -> CompletionCheck:
    """Eligible when the item has at least one non-archived child and every one is done.

    The item's own stored status is ignored, so a manually completed item still reports its
    open children.
    """
    children = tree_order(node.live_children())
    open_children = tuple(child for child in children if not is_done(child))
    return CompletionCheck(
        eligible=bool(children) and not open_children, open_children=open_children
    )


def completed_with_open_items(node: QuestNode) -> bool:
    return node.completed and not node.is_task and bool(completion_check(node).open_children)


def check_can_complete(node: QuestNode, *, override: bool) -> CompletionCheck:
    """Raise `QuestRuleError` when completing needs `override` and it was not given."""
    if node.kind is QuestKind.CHAPTER:
        raise QuestRuleError("a chapter is completed by its tasks")
    if node.archived:
        raise QuestRuleError(f"{_label(node.kind)} {node.id} is archived")
    check = completion_check(node)
    if node.is_task or check.eligible or override or node.completed:
        return check
    if check.open_children:
        names = ", ".join(f"{_label(child.kind)} {child.title!r}" for child in check.open_children)
        raise NeedsOverrideError(f"not everything is done yet ({names}); pass override to complete")
    raise NeedsOverrideError("nothing has been added yet; pass override to complete")


# --- Progress (plan §4.5) --------------------------------------------------------------------


def progress(node: QuestNode) -> float | None:
    """Weighted progress in [0, 1], or None when a container has no non-archived children.

    A task is 1 when completed, else 0 (in progress counts 0). A completed container is 1. A
    child's weight defaults to 1 and a child with no progress (None) counts as 0.
    """
    if node.is_task:
        return 1.0 if node.completed else 0.0
    if node.completed:
        return 1.0
    children = node.live_children()
    if not children:
        return None
    total = 0.0
    weighted = 0.0
    for child in children:
        weight = child.weight if child.weight is not None else 1.0
        total += weight
        weighted += weight * (progress(child) or 0.0)
    return weighted / total if total > 0 else None


def normalized_weights(children: Sequence[QuestNode]) -> dict[int, float]:
    """Share of each non-archived child's weight among its siblings, keyed by position in
    `children` (shown as a percentage)."""
    live = [(index, child) for index, child in enumerate(children) if not child.archived]
    weights = {index: child.weight if child.weight is not None else 1.0 for index, child in live}
    total = sum(weights.values())
    return {index: (weight / total if total > 0 else 0.0) for index, weight in weights.items()}


@dataclass(frozen=True, slots=True)
class TaskCounts:
    done: int
    total: int


def task_counts(node: QuestNode) -> TaskCounts:
    tasks = list(walk_tasks(node))
    return TaskCounts(done=sum(1 for task in tasks if task.completed), total=len(tasks))


# --- Next action (plan §4.6) -----------------------------------------------------------------

_PRIORITY_RANK = {TaskPriority.HIGH: 0, TaskPriority.NORMAL: 1, TaskPriority.LOW: 2}


def next_action(node: QuestNode, now: datetime) -> QuestNode | None:
    """The task to work on next under `node`.

    1. The open task with the earliest scheduled block that has not ended yet.
    2. Else the first `in_progress` task in tree order.
    3. Else the first `todo` task by nearest due date (undated last), then higher priority,
       then tree order.
    4. Else None.
    """
    now = as_utc(now)
    tasks = [task for task in walk_tasks(node) if not task.completed]
    upcoming = [
        (as_utc(block.start_at), order, task)
        for order, task in enumerate(tasks)
        for block in task.blocks
        if block.status is TimeBlockStatus.SCHEDULED and as_utc(block.end_at) > now
    ]
    if upcoming:
        return min(upcoming, key=lambda item: (item[0], item[1]))[2]
    for task in tasks:
        if task.status is TaskStatus.IN_PROGRESS:
            return task
    todo = [(order, task) for order, task in enumerate(tasks) if task.status is TaskStatus.TODO]
    if not todo:
        return None
    return min(
        todo,
        key=lambda item: (
            item[1].due_on is None,
            item[1].due_on or date.max,
            _PRIORITY_RANK[item[1].priority],
            item[0],
        ),
    )[1]


# --- Time blocks (plan §4.7) -----------------------------------------------------------------


def as_utc(value: datetime) -> datetime:
    """Treat a naive datetime (as SQLite returns it) as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def block_minutes(block: BlockView) -> float:
    return (as_utc(block.end_at) - as_utc(block.start_at)).total_seconds() / 60


def planned_minutes(node: QuestNode) -> float:
    """Σ (end − start) over non-cancelled blocks of the non-archived tasks under `node`.

    Planned time is what was scheduled, never actual effort.
    """
    return sum(
        block_minutes(block)
        for task in walk_tasks(node)
        for block in task.blocks
        if block.status is not TimeBlockStatus.CANCELLED
    )


def is_unconfirmed(block: BlockView, now: datetime) -> bool:
    """A block still `scheduled` after its end has passed."""
    return block.status is TimeBlockStatus.SCHEDULED and as_utc(block.end_at) <= as_utc(now)


def check_block_window(start_at: datetime, end_at: datetime) -> None:
    if as_utc(end_at) <= as_utc(start_at):
        raise QuestRuleError("a time block must end after it starts")


def check_can_schedule(task_status: TaskStatus, *, task_archived: bool = False) -> None:
    if task_status is TaskStatus.COMPLETED:
        raise QuestRuleError("a completed task takes no new time blocks; reopen it first")
    if task_archived:
        raise QuestRuleError("an archived task takes no new time blocks")


@dataclass(frozen=True, slots=True)
class BlockOutcome:
    block_status: TimeBlockStatus
    task: TaskTimes


def complete_block(task: TaskTimes, now: datetime) -> BlockOutcome:
    """A session happened: the block is completed and a `todo` task moves to `in_progress`.

    Nothing else changes; in particular the task is never completed here.
    """
    if task.status is TaskStatus.TODO:
        task = transition_task(task, TaskStatus.IN_PROGRESS, now)
    return BlockOutcome(block_status=TimeBlockStatus.COMPLETED, task=task)


def overlapping_ids(blocks: Sequence[BlockView]) -> frozenset[int]:
    """Ids of non-cancelled blocks that overlap another non-cancelled block."""
    live = sorted(
        (block for block in blocks if block.status is not TimeBlockStatus.CANCELLED),
        key=lambda block: as_utc(block.start_at),
    )
    found: set[int] = set()
    for index, block in enumerate(live):
        for other in live[index + 1 :]:
            if as_utc(other.start_at) >= as_utc(block.end_at):
                break
            found.update({block.id, other.id})
    return frozenset(found)


def _label(kind: QuestKind | ParentKind) -> str:
    return str(kind).replace("_", " ")
