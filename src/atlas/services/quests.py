"""Quest use cases: ambitions, goals, milestones, side quests, chapters, and tasks.

Every read builds a `QuestIndex` (all quest rows, loaded once; Atlas is single-user and local)
and asks `atlas.domain.quests` for progress, eligibility, chapter state, and next action.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from atlas.db.models import Ambition, Chapter, Goal, Milestone, SideQuest, Task, TimeBlock
from atlas.domain import (
    ChapterState,
    ParentKind,
    QuestStatus,
    TaskPriority,
    TaskStatus,
    TimeBlockProvider,
    TimeBlockStatus,
)
from atlas.domain.quests import (
    BlockView,
    NeedsOverrideError,
    ParentRef,
    QuestKind,
    QuestNode,
    QuestRuleError,
    TaskTimes,
    as_utc,
    block_minutes,
    check_can_complete,
    check_parent,
    completed_with_open_items,
    completion_check,
    is_unconfirmed,
    next_action,
    node_chapter_state,
    normalized_weights,
    planned_minutes,
    progress,
    task_counts,
    transition_task,
    tree_order,
)
from atlas.services.errors import ConflictError, NotFoundError, ValidationError

ContainerRow = Ambition | Goal | Milestone | SideQuest | Chapter
Key = tuple[QuestKind, int]

CONTAINER_MODELS: dict[QuestKind, type[Any]] = {
    QuestKind.AMBITION: Ambition,
    QuestKind.GOAL: Goal,
    QuestKind.MILESTONE: Milestone,
    QuestKind.SIDE_QUEST: SideQuest,
    QuestKind.CHAPTER: Chapter,
}

TASK_PARENT_COLUMNS: dict[ParentKind, str] = {
    ParentKind.AMBITION: "ambition_id",
    ParentKind.GOAL: "goal_id",
    ParentKind.MILESTONE: "milestone_id",
    ParentKind.CHAPTER: "chapter_id",
    ParentKind.SIDE_QUEST: "side_quest_id",
}

_KIND_OF_PARENT = {kind: QuestKind(kind.value) for kind in ParentKind}


# --- Views returned to the API ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ItemRef:
    kind: QuestKind
    id: int
    title: str


@dataclass(frozen=True, slots=True)
class BlockItem:
    id: int
    task_id: int
    start_at: datetime
    end_at: datetime
    status: TimeBlockStatus
    provider: TimeBlockProvider
    external_event_id: str | None
    created_at: datetime
    updated_at: datetime
    minutes: float
    unconfirmed: bool
    overlaps: bool = False


@dataclass(frozen=True, slots=True)
class TaskView:
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    estimate_minutes: int | None
    due_on: date | None
    weight: float | None
    weight_share: float | None
    position: int
    parent: ItemRef | None
    path: list[ItemRef]
    inbox: bool
    standalone: bool
    organized_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    planned_minutes: float
    block_count: int
    blocks: list[BlockItem] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ContainerView:
    """One ambition, goal, milestone, side quest, or chapter with its computed state."""

    kind: QuestKind
    id: int
    title: str
    description: str | None
    position: int
    weight: float | None
    weight_share: float | None
    status: QuestStatus | None
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    parent: ItemRef | None
    path: list[ItemRef]
    progress: float | None
    done_tasks: int
    total_tasks: int
    planned_minutes: float
    eligible: bool
    open_children: list[ItemRef]
    completed_with_open_items: bool
    next_action: TaskView | None
    target_on: date | None = None
    due_on: date | None = None
    success_description: str | None = None
    ambition_id: int | None = None
    goal_id: int | None = None
    milestone_id: int | None = None
    side_quest_id: int | None = None
    state: ChapterState | None = None
    goal_count: int = 0
    milestone_count: int = 0
    chapter_count: int = 0
    task_count: int = 0


@dataclass(frozen=True, slots=True)
class PromoteResult:
    kind: QuestKind
    id: int
    title: str


# --- The index -------------------------------------------------------------------------------


class QuestIndex:
    """All quest rows in memory, with parent → children links and tree builders."""

    def __init__(self, session: Session) -> None:
        self.rows: dict[QuestKind, dict[int, Any]] = {
            kind: {row.id: row for row in session.exec(select(model)).all()}
            for kind, model in CONTAINER_MODELS.items()
        }
        self.rows[QuestKind.TASK] = {row.id: row for row in session.exec(select(Task)).all()}
        self.blocks: dict[int, list[TimeBlock]] = {}
        for block in session.exec(select(TimeBlock).order_by(TimeBlock.start_at)).all():
            self.blocks.setdefault(block.task_id, []).append(block)
        self.children: dict[Key, list[Key]] = {}
        for kind, rows in self.rows.items():
            for row in rows.values():
                parent = parent_key(kind, row)
                if parent is not None:
                    self.children.setdefault(parent, []).append((kind, row.id))
        self._nodes: dict[Key, QuestNode] = {}

    def row(self, kind: QuestKind, item_id: int) -> Any:
        row = self.rows[kind].get(item_id)
        if row is None:
            raise NotFoundError(kind.value, item_id)
        return row

    def ref(self, kind: QuestKind, item_id: int) -> ItemRef:
        return ItemRef(kind=kind, id=item_id, title=self.row(kind, item_id).title)

    def child_keys(self, kind: QuestKind, item_id: int) -> list[Key]:
        return list(self.children.get((kind, item_id), []))

    def node(self, kind: QuestKind, item_id: int) -> QuestNode:
        key = (kind, item_id)
        if key not in self._nodes:
            self._nodes[key] = self._build(kind, item_id)
        return self._nodes[key]

    def _build(self, kind: QuestKind, item_id: int) -> QuestNode:
        row = self.row(kind, item_id)
        if kind is QuestKind.TASK:
            status = TaskStatus(row.status)
            return QuestNode(
                kind=kind,
                id=row.id,
                title=row.title,
                weight=row.weight,
                position=row.position,
                completed=status is TaskStatus.COMPLETED,
                archived=row.archived_at is not None,
                status=status,
                priority=TaskPriority(row.priority),
                due_on=row.due_on,
                blocks=tuple(block_view(block) for block in self.blocks.get(row.id, [])),
            )
        status = getattr(row, "status", None)
        return QuestNode(
            kind=kind,
            id=row.id,
            title=row.title,
            weight=getattr(row, "weight", None),
            position=row.position,
            completed=status is not None and QuestStatus(status) is QuestStatus.COMPLETED,
            archived=row.archived_at is not None,
            children=tuple(self.node(*child) for child in self.child_keys(kind, item_id)),
        )

    def parent_ref(self, kind: QuestKind, row: Any) -> ItemRef | None:
        parent = parent_key(kind, row)
        return None if parent is None else self.ref(*parent)

    def path(self, kind: QuestKind, row: Any) -> list[ItemRef]:
        refs: list[ItemRef] = []
        parent = parent_key(kind, row)
        while parent is not None:
            parent_row = self.row(*parent)
            refs.append(ItemRef(kind=parent[0], id=parent[1], title=parent_row.title))
            parent = parent_key(parent[0], parent_row)
        return list(reversed(refs))

    def weight_share(self, kind: QuestKind, row: Any) -> float | None:
        parent = parent_key(kind, row)
        if parent is None or row.archived_at is not None:
            return None
        siblings = [self.node(*child) for child in self.child_keys(*parent)]
        shares = normalized_weights(siblings)
        for index, sibling in enumerate(siblings):
            if sibling.kind is kind and sibling.id == row.id:
                return shares.get(index)
        return None

    def ordered_children(self, kind: QuestKind, item_id: int, child_kind: QuestKind) -> list[int]:
        nodes = [self.node(*key) for key in self.child_keys(kind, item_id) if key[0] is child_kind]
        return [node.id for node in tree_order(nodes)]

    def task_view(self, task_id: int, now: datetime, *, with_blocks: bool = False) -> TaskView:
        row: Task = self.row(QuestKind.TASK, task_id)
        node = self.node(QuestKind.TASK, task_id)
        rows = self.blocks.get(task_id, [])
        parent = self.parent_ref(QuestKind.TASK, row)
        return TaskView(
            id=row.id,
            title=row.title,
            description=row.description,
            status=TaskStatus(row.status),
            priority=TaskPriority(row.priority),
            estimate_minutes=row.estimate_minutes,
            due_on=row.due_on,
            weight=row.weight,
            weight_share=self.weight_share(QuestKind.TASK, row),
            position=row.position,
            parent=parent,
            path=self.path(QuestKind.TASK, row),
            inbox=parent is None and row.organized_at is None,
            standalone=parent is None and row.organized_at is not None,
            organized_at=_utc(row.organized_at),
            started_at=_utc(row.started_at),
            completed_at=_utc(row.completed_at),
            archived_at=_utc(row.archived_at),
            created_at=as_utc(row.created_at),
            updated_at=as_utc(row.updated_at),
            planned_minutes=sum(
                block_minutes(block)
                for block in node.blocks
                if block.status is not TimeBlockStatus.CANCELLED
            ),
            block_count=len(rows),
            blocks=[block_item(block, now) for block in rows] if with_blocks else [],
        )

    def container_view(self, kind: QuestKind, item_id: int, now: datetime) -> ContainerView:
        row = self.row(kind, item_id)
        node = self.node(kind, item_id)
        counts = task_counts(node)
        check = completion_check(node)
        action = next_action(node, now)
        live = [key for key in self.child_keys(kind, item_id) if not self.node(*key).archived]
        status = getattr(row, "status", None)
        return ContainerView(
            kind=kind,
            id=row.id,
            title=row.title,
            description=row.description,
            position=row.position,
            weight=getattr(row, "weight", None),
            weight_share=self.weight_share(kind, row),
            status=QuestStatus(status) if status is not None else None,
            completed_at=_utc(getattr(row, "completed_at", None)),
            archived_at=_utc(row.archived_at),
            created_at=as_utc(row.created_at),
            updated_at=as_utc(row.updated_at),
            parent=self.parent_ref(kind, row),
            path=self.path(kind, row),
            progress=progress(node),
            done_tasks=counts.done,
            total_tasks=counts.total,
            planned_minutes=planned_minutes(node),
            eligible=check.eligible,
            open_children=[
                ItemRef(child.kind, child.id, child.title) for child in check.open_children
            ],
            completed_with_open_items=completed_with_open_items(node),
            next_action=None if action is None else self.task_view(action.id, now),
            target_on=getattr(row, "target_on", None),
            due_on=getattr(row, "due_on", None),
            success_description=getattr(row, "success_description", None),
            ambition_id=getattr(row, "ambition_id", None),
            goal_id=getattr(row, "goal_id", None),
            milestone_id=getattr(row, "milestone_id", None),
            side_quest_id=getattr(row, "side_quest_id", None),
            state=node_chapter_state(node) if kind is QuestKind.CHAPTER else None,
            goal_count=sum(1 for key in live if key[0] is QuestKind.GOAL),
            milestone_count=sum(1 for key in live if key[0] is QuestKind.MILESTONE),
            chapter_count=sum(1 for key in live if key[0] is QuestKind.CHAPTER),
            task_count=sum(1 for key in live if key[0] is QuestKind.TASK),
        )


def parent_key(kind: QuestKind, row: Any) -> Key | None:
    if kind is QuestKind.GOAL and row.ambition_id is not None:
        return (QuestKind.AMBITION, row.ambition_id)
    if kind is QuestKind.MILESTONE:
        return (QuestKind.GOAL, row.goal_id)
    if kind is QuestKind.CHAPTER:
        if row.milestone_id is not None:
            return (QuestKind.MILESTONE, row.milestone_id)
        return (QuestKind.SIDE_QUEST, row.side_quest_id)
    if kind is QuestKind.TASK:
        for parent_kind, column in TASK_PARENT_COLUMNS.items():
            value = getattr(row, column)
            if value is not None:
                return (_KIND_OF_PARENT[parent_kind], value)
    return None


def block_view(block: TimeBlock) -> BlockView:
    return BlockView(
        id=block.id,
        task_id=block.task_id,
        start_at=as_utc(block.start_at),
        end_at=as_utc(block.end_at),
        status=TimeBlockStatus(block.status),
    )


def block_item(block: TimeBlock, now: datetime, *, overlaps: bool = False) -> BlockItem:
    view = block_view(block)
    return BlockItem(
        id=block.id,
        task_id=block.task_id,
        start_at=view.start_at,
        end_at=view.end_at,
        status=view.status,
        provider=TimeBlockProvider(block.provider),
        external_event_id=block.external_event_id,
        created_at=as_utc(block.created_at),
        updated_at=as_utc(block.updated_at),
        minutes=block_minutes(view),
        unconfirmed=is_unconfirmed(view, now),
        overlaps=overlaps,
    )


# --- Containers ------------------------------------------------------------------------------


def list_containers(
    session: Session,
    kind: QuestKind,
    *,
    include_archived: bool = False,
    ambition_id: int | None = None,
    now: datetime | None = None,
) -> list[ContainerView]:
    now = _now(now)
    index = QuestIndex(session)
    rows = list(index.rows[kind].values())
    if not include_archived:
        rows = [row for row in rows if row.archived_at is None]
    if ambition_id is not None:
        rows = [row for row in rows if getattr(row, "ambition_id", None) == ambition_id]
    rows.sort(key=lambda row: (row.position, row.id))
    return [index.container_view(kind, row.id, now) for row in rows]


def get_container(
    session: Session, kind: QuestKind, item_id: int, *, now: datetime | None = None
) -> ContainerView:
    return QuestIndex(session).container_view(kind, item_id, _now(now))


def create_container(
    session: Session,
    kind: QuestKind,
    fields: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> ContainerView:
    now = _now(now)
    model = CONTAINER_MODELS[kind]
    data = dict(fields)
    title = _title(data.pop("title", None))
    position = data.pop("position", None)
    _check_weight(data.get("weight"))
    row = model(title=title, created_at=now, updated_at=now)
    _apply_parent(session, kind, row, data, creating=True)
    for key, value in data.items():
        _set_field(row, key, value)
    row.position = position if position is not None else _next_position(session, kind, row)
    session.add(row)
    session.commit()
    session.refresh(row)
    return get_container(session, kind, row.id, now=now)


def update_container(
    session: Session,
    kind: QuestKind,
    item_id: int,
    fields: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> ContainerView:
    now = _now(now)
    row = _get_row(session, kind, item_id)
    data = dict(fields)
    if "title" in data:
        row.title = _title(data.pop("title"))
    if "weight" in data:
        _check_weight(data["weight"])
    archived = data.pop("archived", None)
    _apply_parent(session, kind, row, data, creating=False)
    for key, value in data.items():
        if key == "position" and value is None:
            continue
        _set_field(row, key, value)
    if archived is not None:
        _set_archived(kind, row, bool(archived), now)
    row.updated_at = now
    session.add(row)
    session.commit()
    return get_container(session, kind, item_id, now=now)


def delete_container(session: Session, kind: QuestKind, item_id: int) -> None:
    index = QuestIndex(session)
    index.row(kind, item_id)
    children = index.child_keys(kind, item_id)
    if children:
        raise ConflictError(
            f"{_label(kind)} {item_id} still has {len(children)} item(s) under it; "
            "archive it instead or remove them first"
        )
    session.delete(session.get(CONTAINER_MODELS[kind], item_id))
    session.commit()


def complete_container(
    session: Session,
    kind: QuestKind,
    item_id: int,
    *,
    override: bool = False,
    now: datetime | None = None,
) -> ContainerView:
    now = _now(now)
    index = QuestIndex(session)
    try:
        check_can_complete(index.node(kind, item_id), override=override)
    except NeedsOverrideError as exc:
        raise ConflictError(str(exc)) from exc
    except QuestRuleError as exc:
        raise ValidationError(str(exc)) from exc
    row = _get_row(session, kind, item_id)
    if QuestStatus(row.status) is not QuestStatus.COMPLETED:
        row.status = QuestStatus.COMPLETED
        row.completed_at = now
        row.updated_at = now
        session.add(row)
        session.commit()
    return get_container(session, kind, item_id, now=now)


def reopen_container(
    session: Session, kind: QuestKind, item_id: int, *, now: datetime | None = None
) -> ContainerView:
    now = _now(now)
    if kind is QuestKind.CHAPTER:
        raise ValidationError("a chapter is completed by its tasks")
    row = _get_row(session, kind, item_id)
    if row.archived_at is not None:
        raise ValidationError(f"{_label(kind)} {item_id} is archived")
    if QuestStatus(row.status) is QuestStatus.COMPLETED:
        row.status = QuestStatus.ACTIVE
        row.completed_at = None
        row.updated_at = now
        session.add(row)
        session.commit()
    return get_container(session, kind, item_id, now=now)


# --- Tasks -----------------------------------------------------------------------------------


def list_tasks(
    session: Session,
    *,
    parent_kind: ParentKind | None = None,
    parent_id: int | None = None,
    status: TaskStatus | None = None,
    inbox: bool | None = None,
    standalone: bool | None = None,
    due_on: date | None = None,
    include_archived: bool = False,
    now: datetime | None = None,
) -> list[TaskView]:
    now = _now(now)
    if (parent_kind is None) != (parent_id is None):
        raise ValidationError("parent_kind and parent_id go together")
    index = QuestIndex(session)
    views = [index.task_view(task_id, now) for task_id in index.rows[QuestKind.TASK]]
    if parent_kind is not None:
        views = [
            view
            for view in views
            if view.parent is not None
            and view.parent.kind is _KIND_OF_PARENT[parent_kind]
            and view.parent.id == parent_id
        ]
    if status is not None:
        views = [view for view in views if view.status is status]
    if inbox is not None:
        views = [view for view in views if view.inbox is inbox]
    if standalone is not None:
        views = [view for view in views if view.standalone is standalone]
    if due_on is not None:
        views = [view for view in views if view.due_on == due_on]
    if not include_archived:
        views = [view for view in views if view.archived_at is None]
    return sorted(views, key=lambda view: (view.position, view.id))


def get_task(session: Session, task_id: int, *, now: datetime | None = None) -> TaskView:
    return QuestIndex(session).task_view(task_id, _now(now), with_blocks=True)


def create_task(
    session: Session,
    *,
    title: str,
    description: str | None = None,
    parent_kind: ParentKind | None = None,
    parent_id: int | None = None,
    standalone: bool = False,
    priority: TaskPriority = TaskPriority.NORMAL,
    estimate_minutes: int | None = None,
    due_on: date | None = None,
    weight: float | None = None,
    position: int | None = None,
    now: datetime | None = None,
) -> TaskView:
    """Create a task. With no parent and not standalone it lands in the Inbox."""
    now = _now(now)
    _check_weight(weight)
    _check_estimate(estimate_minutes)
    if (parent_kind is None) != (parent_id is None):
        raise ValidationError("parent_kind and parent_id go together")
    if parent_kind is not None and standalone:
        raise ValidationError("a task with a parent is not standalone")
    row = Task(
        title=_title(title),
        description=description,
        priority=TaskPriority(priority),
        estimate_minutes=estimate_minutes,
        due_on=due_on,
        weight=weight,
        created_at=now,
        updated_at=now,
    )
    if parent_kind is not None and parent_id is not None:
        _set_task_parent(session, row, parent_kind, parent_id)
        row.organized_at = now
    elif standalone:
        row.organized_at = now
    row.position = (
        position if position is not None else _next_position(session, QuestKind.TASK, row)
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return get_task(session, row.id, now=now)


def update_task(
    session: Session,
    task_id: int,
    fields: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> TaskView:
    now = _now(now)
    row = _get_row(session, QuestKind.TASK, task_id)
    data = dict(fields)
    if "title" in data:
        row.title = _title(data.pop("title"))
    if "weight" in data:
        _check_weight(data["weight"])
    if "estimate_minutes" in data:
        _check_estimate(data["estimate_minutes"])
    status = data.pop("status", None)
    archived = data.pop("archived", None)
    for key in ("description", "priority", "estimate_minutes", "due_on", "weight", "position"):
        if key in data:
            if key == "position" and data[key] is None:
                continue
            setattr(row, key, data.pop(key))
    if data:
        raise ValidationError(f"cannot update {', '.join(sorted(data))} on a task")
    if status is not None:
        _apply_task_status(row, TaskStatus(status), now)
    if archived is not None:
        row.archived_at = now if archived else None
    row.updated_at = now
    session.add(row)
    session.commit()
    return get_task(session, task_id, now=now)


def delete_task(session: Session, task_id: int) -> None:
    row = _get_row(session, QuestKind.TASK, task_id)
    if parent_key(QuestKind.TASK, row) is not None or row.organized_at is not None:
        raise ConflictError("only an Inbox task can be deleted; archive it instead")
    if session.exec(select(TimeBlock).where(TimeBlock.task_id == task_id)).first() is not None:
        raise ConflictError("this task has time blocks; archive it instead")
    session.delete(row)
    session.commit()


def organize_task(
    session: Session,
    task_id: int,
    *,
    parent_kind: ParentKind | None = None,
    parent_id: int | None = None,
    standalone: bool = False,
    now: datetime | None = None,
) -> TaskView:
    """File a task under a parent or as standalone. Its id, status, and blocks are kept."""
    now = _now(now)
    row = _get_row(session, QuestKind.TASK, task_id)
    if standalone == (parent_kind is not None or parent_id is not None):
        raise ValidationError("give either parent_kind and parent_id, or standalone")
    if standalone:
        for column in TASK_PARENT_COLUMNS.values():
            setattr(row, column, None)
    else:
        if parent_kind is None or parent_id is None:
            raise ValidationError("parent_kind and parent_id go together")
        _set_task_parent(session, row, parent_kind, parent_id)
    if row.organized_at is None:
        row.organized_at = now
    row.position = _next_position(session, QuestKind.TASK, row, exclude_id=row.id)
    row.updated_at = now
    session.add(row)
    session.commit()
    return get_task(session, task_id, now=now)


def promote_task(
    session: Session,
    task_id: int,
    *,
    kind: QuestKind,
    parent_kind: ParentKind | None = None,
    parent_id: int | None = None,
    now: datetime | None = None,
) -> PromoteResult:
    """Turn an Inbox task into a new container (title and description carried over) and
    delete the task. Refused once the task has time blocks."""
    now = _now(now)
    row = _get_row(session, QuestKind.TASK, task_id)
    if parent_key(QuestKind.TASK, row) is not None or row.organized_at is not None:
        raise ValidationError("only an Inbox task can be turned into something else")
    if session.exec(select(TimeBlock).where(TimeBlock.task_id == task_id)).first() is not None:
        raise ValidationError(
            "this task already has time blocks, so it cannot become something else; "
            "organize it instead"
        )
    if kind is QuestKind.TASK:
        raise ValidationError("a task is already a task; organize it instead")
    fields: dict[str, Any] = {"title": row.title, "description": row.description}
    fields.update(_promote_parent_fields(kind, parent_kind, parent_id))
    session.delete(row)
    session.flush()
    try:
        created = create_container(session, kind, fields, now=now)
    except Exception:
        session.rollback()
        raise
    return PromoteResult(kind=kind, id=created.id, title=created.title)


# --- Helpers ---------------------------------------------------------------------------------


def _promote_parent_fields(
    kind: QuestKind, parent_kind: ParentKind | None, parent_id: int | None
) -> dict[str, Any]:
    if kind in (QuestKind.AMBITION, QuestKind.SIDE_QUEST):
        if parent_kind is not None or parent_id is not None:
            raise ValidationError(f"a {_label(kind)} has no parent")
        return {}
    if kind is QuestKind.GOAL:
        if parent_kind not in (None, ParentKind.AMBITION):
            raise ValidationError("a goal can only belong to an ambition")
        return {"ambition_id": parent_id}
    if kind is QuestKind.MILESTONE:
        if parent_kind not in (None, ParentKind.GOAL) or parent_id is None:
            raise ValidationError("a milestone needs a goal (parent_id)")
        return {"goal_id": parent_id}
    if parent_kind is ParentKind.MILESTONE and parent_id is not None:
        return {"milestone_id": parent_id}
    if parent_kind is ParentKind.SIDE_QUEST and parent_id is not None:
        return {"side_quest_id": parent_id}
    raise ValidationError("a chapter needs a milestone or side quest (parent_kind, parent_id)")


def _apply_parent(
    session: Session, kind: QuestKind, row: Any, data: dict[str, Any], *, creating: bool
) -> None:
    """Validate and set a container's parent column(s) from `data` (popping them)."""
    columns = _PARENT_COLUMNS.get(kind, ())
    if creating or any(column in data for column in columns):
        values = {column: data.pop(column, None) for column in columns}
        given = [(column, value) for column, value in values.items() if value is not None]
        if len(given) > 1:
            raise ValidationError(f"a {_label(kind)} belongs to one parent, not two")
        parent = None
        if given:
            column, value = given[0]
            parent = _parent_ref(session, _COLUMN_PARENT[column], value)
        _check(kind, parent)
        for column, value in values.items():
            setattr(row, column, value)
    for column in _COLUMN_PARENT:
        if column in data:
            raise ValidationError(f"a {_label(kind)} has no {column}")


_PARENT_COLUMNS: dict[QuestKind, tuple[str, ...]] = {
    QuestKind.GOAL: ("ambition_id",),
    QuestKind.MILESTONE: ("goal_id",),
    QuestKind.CHAPTER: ("milestone_id", "side_quest_id"),
}

_COLUMN_PARENT: dict[str, ParentKind] = {
    "ambition_id": ParentKind.AMBITION,
    "goal_id": ParentKind.GOAL,
    "milestone_id": ParentKind.MILESTONE,
    "side_quest_id": ParentKind.SIDE_QUEST,
}


def _set_task_parent(session: Session, row: Task, parent_kind: ParentKind, parent_id: int) -> None:
    _check(QuestKind.TASK, _parent_ref(session, ParentKind(parent_kind), parent_id))
    for kind, column in TASK_PARENT_COLUMNS.items():
        setattr(row, column, parent_id if kind is ParentKind(parent_kind) else None)


def _parent_ref(session: Session, parent_kind: ParentKind, parent_id: int) -> ParentRef:
    model = CONTAINER_MODELS[_KIND_OF_PARENT[parent_kind]]
    parent = session.get(model, parent_id)
    if parent is None:
        raise ValidationError(f"{_label(parent_kind)} {parent_id} does not exist")
    return ParentRef(kind=parent_kind, id=parent_id, archived=parent.archived_at is not None)


def _check(kind: QuestKind, parent: ParentRef | None) -> None:
    try:
        check_parent(kind, parent)
    except QuestRuleError as exc:
        raise ValidationError(str(exc)) from exc


def _apply_task_status(row: Task, status: TaskStatus, now: datetime) -> None:
    apply_task_times(row, transition_task(task_times(row), status, now))


def task_times(row: Task) -> TaskTimes:
    return TaskTimes(TaskStatus(row.status), row.started_at, row.completed_at)


def apply_task_times(row: Task, times: TaskTimes) -> None:
    row.status = times.status
    row.started_at = times.started_at
    row.completed_at = times.completed_at


def _set_archived(kind: QuestKind, row: Any, archived: bool, now: datetime) -> None:
    if archived:
        if row.archived_at is None:
            row.archived_at = now
        if kind is not QuestKind.CHAPTER:
            row.status = QuestStatus.ARCHIVED
        return
    row.archived_at = None
    if kind is not QuestKind.CHAPTER:
        row.status = QuestStatus.COMPLETED if row.completed_at is not None else QuestStatus.ACTIVE


def _set_field(row: Any, key: str, value: Any) -> None:
    if key not in type(row).model_fields or key in {
        "id",
        "status",
        "completed_at",
        "archived_at",
        "created_at",
        "updated_at",
    }:
        raise ValidationError(f"cannot set {key} on a {type(row).__tablename__}")
    setattr(row, key, value)


def _next_position(
    session: Session, kind: QuestKind, row: Any, *, exclude_id: int | None = None
) -> int:
    index = QuestIndex(session)
    parent = parent_key(kind, row)
    if parent is not None:
        siblings = [index.row(*key) for key in index.child_keys(*parent) if key[0] is kind]
    elif kind is QuestKind.TASK:
        organized = row.organized_at is not None
        siblings = [
            other
            for other in index.rows[kind].values()
            if parent_key(kind, other) is None and (other.organized_at is not None) == organized
        ]
    else:
        siblings = [other for other in index.rows[kind].values() if parent_key(kind, other) is None]
    positions = [other.position for other in siblings if other.id != exclude_id]
    return max(positions, default=-1) + 1


def _get_row(session: Session, kind: QuestKind, item_id: int) -> Any:
    model = Task if kind is QuestKind.TASK else CONTAINER_MODELS[kind]
    row = session.get(model, item_id)
    if row is None:
        raise NotFoundError(kind.value, item_id)
    return row


def _title(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("a title is required")
    return value.strip()


def _check_weight(weight: Any) -> None:
    if weight is not None and not weight > 0:
        raise ValidationError("weight must be greater than zero")


def _check_estimate(minutes: Any) -> None:
    if minutes is not None and not minutes > 0:
        raise ValidationError("estimate_minutes must be greater than zero")


def _now(now: datetime | None) -> datetime:
    return as_utc(now) if now is not None else datetime.now(UTC)


def _utc(value: datetime | None) -> datetime | None:
    return None if value is None else as_utc(value)


def _label(kind: QuestKind | ParentKind) -> str:
    return str(kind).replace("_", " ")
