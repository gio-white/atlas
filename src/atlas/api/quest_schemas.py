"""Request and response bodies for the quest and time block endpoints (integer ids)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from atlas.domain import (
    ChapterState,
    ParentKind,
    QuestStatus,
    TaskPriority,
    TaskStatus,
    TimeBlockProvider,
    TimeBlockStatus,
)
from atlas.domain.quests import QuestKind

# --- Responses -------------------------------------------------------------------------------


class _Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ItemRefOut(_Read):
    kind: QuestKind
    id: int
    title: str


class TimeBlockOut(_Read):
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
    overlaps: bool


class TaskOut(_Read):
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
    parent: ItemRefOut | None
    path: list[ItemRefOut]
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


class TaskDetailOut(TaskOut):
    blocks: list[TimeBlockOut]


class _QuestState(_Read):
    id: int
    title: str
    description: str | None
    position: int
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    path: list[ItemRefOut]
    progress: float | None
    done_tasks: int
    total_tasks: int
    planned_minutes: float
    eligible: bool
    open_children: list[ItemRefOut]
    next_action: TaskOut | None


class _Completable(_QuestState):
    status: QuestStatus
    completed_at: datetime | None
    completed_with_open_items: bool


class AmbitionOut(_Completable):
    target_on: date | None
    weight: float | None
    goal_count: int
    task_count: int


class GoalOut(_Completable):
    ambition_id: int | None
    success_description: str | None
    due_on: date | None
    weight: float | None
    weight_share: float | None
    milestone_count: int
    task_count: int


class MilestoneOut(_Completable):
    goal_id: int
    due_on: date | None
    weight: float | None
    weight_share: float | None
    chapter_count: int
    task_count: int


class SideQuestOut(_Completable):
    due_on: date | None
    chapter_count: int
    task_count: int


class ChapterOut(_QuestState):
    milestone_id: int | None
    side_quest_id: int | None
    weight: float | None
    weight_share: float | None
    state: ChapterState
    task_count: int


class PromoteOut(_Read):
    kind: QuestKind
    id: int
    title: str


class ChapterTreeOut(_Read):
    chapter: ChapterOut
    tasks: list[TaskOut]


class MilestoneTreeOut(_Read):
    milestone: MilestoneOut
    chapters: list[ChapterTreeOut]
    tasks: list[TaskOut]


class AmbitionSectionOut(_Read):
    ambition: AmbitionOut
    goals: list[GoalOut]
    tasks: list[TaskOut]


class MainQuestsOut(_Read):
    ambitions: list[AmbitionSectionOut]
    independent_goals: list[GoalOut]


class GoalTreeOut(_Read):
    goal: GoalOut
    milestones: list[MilestoneTreeOut]
    tasks: list[TaskOut]


class SideQuestTreeOut(_Read):
    side_quest: SideQuestOut
    chapters: list[ChapterTreeOut]
    tasks: list[TaskOut]


class SideQuestsOut(_Read):
    side_quests: list[SideQuestOut]
    standalone_tasks: list[TaskOut]


class InboxOut(_Read):
    count: int
    tasks: list[TaskOut]


class ScheduledBlockOut(_Read):
    block: TimeBlockOut
    task: TaskOut


class TodayOut(_Read):
    date: date
    blocks: list[ScheduledBlockOut]
    unconfirmed: list[ScheduledBlockOut]
    due_today: list[TaskOut]
    up_next: list[TaskOut]


class CalendarOut(_Read):
    start: datetime
    end: datetime
    blocks: list[ScheduledBlockOut]


# --- Requests --------------------------------------------------------------------------------


class _Write(BaseModel):
    model_config = ConfigDict(extra="forbid")


Weight = Field(default=None, gt=0)


class AmbitionCreate(_Write):
    title: str
    description: str | None = None
    target_on: date | None = None
    weight: float | None = Weight
    position: int | None = None


class AmbitionUpdate(_Write):
    title: str | None = None
    description: str | None = None
    target_on: date | None = None
    weight: float | None = Weight
    position: int | None = None
    archived: bool | None = None


class GoalCreate(_Write):
    title: str
    description: str | None = None
    success_description: str | None = None
    due_on: date | None = None
    ambition_id: int | None = None
    weight: float | None = Weight
    position: int | None = None


class GoalUpdate(_Write):
    title: str | None = None
    description: str | None = None
    success_description: str | None = None
    due_on: date | None = None
    ambition_id: int | None = None
    weight: float | None = Weight
    position: int | None = None
    archived: bool | None = None


class MilestoneCreate(_Write):
    goal_id: int
    title: str
    description: str | None = None
    due_on: date | None = None
    weight: float | None = Weight
    position: int | None = None


class MilestoneUpdate(_Write):
    goal_id: int | None = None
    title: str | None = None
    description: str | None = None
    due_on: date | None = None
    weight: float | None = Weight
    position: int | None = None
    archived: bool | None = None


class SideQuestCreate(_Write):
    title: str
    description: str | None = None
    due_on: date | None = None
    position: int | None = None


class SideQuestUpdate(_Write):
    title: str | None = None
    description: str | None = None
    due_on: date | None = None
    position: int | None = None
    archived: bool | None = None


class ChapterCreate(_Write):
    milestone_id: int | None = None
    side_quest_id: int | None = None
    title: str
    description: str | None = None
    weight: float | None = Weight
    position: int | None = None


class ChapterUpdate(_Write):
    milestone_id: int | None = None
    side_quest_id: int | None = None
    title: str | None = None
    description: str | None = None
    weight: float | None = Weight
    position: int | None = None
    archived: bool | None = None


class CompleteRequest(_Write):
    override: bool = False


class TaskCreate(_Write):
    title: str
    description: str | None = None
    parent_kind: ParentKind | None = None
    parent_id: int | None = None
    standalone: bool = False
    priority: TaskPriority = TaskPriority.NORMAL
    estimate_minutes: int | None = Field(default=None, gt=0)
    due_on: date | None = None
    weight: float | None = Weight
    position: int | None = None


class TaskUpdate(_Write):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    estimate_minutes: int | None = Field(default=None, gt=0)
    due_on: date | None = None
    weight: float | None = Weight
    position: int | None = None
    archived: bool | None = None


class TaskOrganize(_Write):
    parent_kind: ParentKind | None = None
    parent_id: int | None = None
    standalone: bool = False


class TaskPromote(_Write):
    kind: QuestKind
    parent_kind: ParentKind | None = None
    parent_id: int | None = None


class TimeBlockCreate(_Write):
    task_id: int
    start_at: datetime
    end_at: datetime


class TimeBlockUpdate(_Write):
    start_at: datetime | None = None
    end_at: datetime | None = None
