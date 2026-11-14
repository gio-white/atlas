from datetime import UTC, date, datetime

from sqlalchemy import JSON, CheckConstraint, Column, Index, LargeBinary, text
from sqlmodel import Field, SQLModel

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    HabitKind,
    LibraryKind,
    LibraryStatus,
    MetricOrigin,
    Period,
    QuestStatus,
    ScreenBudgetTargetKind,
    ScreenJudgment,
    SleepStage,
    Source,
    TaskPriority,
    TaskStatus,
    TimeBlockProvider,
    TimeBlockStatus,
    TimeOfDay,
    ValueType,
)


class Metric(SQLModel, table=True):
    __tablename__ = "metric"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    value_type: ValueType
    unit: str | None = None
    aggregation: Aggregation
    direction: Direction
    origin: MetricOrigin = MetricOrigin.MANUAL
    archived_at: datetime | None = None


class Entry(SQLModel, table=True):
    __tablename__ = "entry"
    __table_args__ = (Index("ix_entry_metric_id_occurred_on", "metric_id", "occurred_on"),)

    id: int | None = Field(default=None, primary_key=True)
    metric_id: int = Field(foreign_key="metric.id")
    occurred_on: date
    occurred_at: datetime | None = None
    value_num: float | None = None
    value_bool: bool | None = None
    value_text: str | None = None
    note: str | None = None
    source: Source
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Habit(SQLModel, table=True):
    __tablename__ = "habit"

    id: int | None = Field(default=None, primary_key=True)
    metric_id: int = Field(foreign_key="metric.id")
    slug: str = Field(unique=True, index=True)
    name: str
    period: Period
    target_value: float
    comparator: Comparator
    weekdays: list[int] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    active_from: date
    active_to: date | None = None
    kind: HabitKind = HabitKind.COUNT
    time_of_day: TimeOfDay = TimeOfDay.ANYTIME
    archived_at: datetime | None = None


class HabitBreak(SQLModel, table=True):
    __tablename__ = "habit_break"

    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id", index=True)
    start_on: date
    end_on: date
    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScreenCategory(SQLModel, table=True):
    __tablename__ = "screen_category"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    judgment: ScreenJudgment
    archived_at: datetime | None = None


class ScreenApp(SQLModel, table=True):
    __tablename__ = "screen_app"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    category_id: int = Field(foreign_key="screen_category.id")
    metric_id: int = Field(foreign_key="metric.id", unique=True)
    archived_at: datetime | None = None


class ScreenBudget(SQLModel, table=True):
    __tablename__ = "screen_budget"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    target_kind: ScreenBudgetTargetKind
    target_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    active_from: date
    active_to: date | None = None


class ScreenDevice(SQLModel, table=True):
    __tablename__ = "screen_device"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    archived_at: datetime | None = None


class ScreenSession(SQLModel, table=True):
    __tablename__ = "screen_session"
    __table_args__ = (Index("ix_screen_session_app_id_occurred_on", "app_id", "occurred_on"),)

    id: int | None = Field(default=None, primary_key=True)
    app_id: int = Field(foreign_key="screen_app.id")
    device_id: int | None = Field(default=None, foreign_key="screen_device.id")
    started_at: datetime | None = None
    ended_at: datetime | None = None
    minutes: float
    occurred_on: date
    note: str | None = None
    source: Source
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    entry_id: int | None = Field(default=None, foreign_key="entry.id", unique=True)


class LibraryTopic(SQLModel, table=True):
    __tablename__ = "library_topic"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    archived_at: datetime | None = None


class LibraryTitle(SQLModel, table=True):
    __tablename__ = "library_title"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    kind: LibraryKind
    creator: str | None = None
    recommended_by: str | None = None
    status: LibraryStatus = LibraryStatus.QUEUED
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    rating: int | None = None
    link: str | None = None
    image_url: str | None = None
    image_bytes: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    image_media_type: str | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LibraryTitleTopic(SQLModel, table=True):
    __tablename__ = "library_title_topic"

    title_id: int = Field(foreign_key="library_title.id", primary_key=True)
    topic_id: int = Field(foreign_key="library_topic.id", primary_key=True)


class SleepSession(SQLModel, table=True):
    __tablename__ = "sleep_session"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime
    ended_at: datetime
    occurred_on: date = Field(index=True)
    note: str | None = None
    source: Source
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SleepSessionStage(SQLModel, table=True):
    __tablename__ = "sleep_session_stage"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sleep_session.id", index=True)
    stage: SleepStage
    started_at: datetime
    ended_at: datetime


def _utcnow() -> datetime:
    return datetime.now(UTC)


# Enum columns store member names, so CHECK constraints compare against names.
_TASK_COMPLETED = TaskStatus.COMPLETED.name


class Ambition(SQLModel, table=True):
    __tablename__ = "ambition"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    target_on: date | None = None
    weight: float | None = None
    position: int = 0
    status: QuestStatus = QuestStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Goal(SQLModel, table=True):
    __tablename__ = "goal"

    id: int | None = Field(default=None, primary_key=True)
    ambition_id: int | None = Field(
        default=None, foreign_key="ambition.id", ondelete="RESTRICT", index=True
    )
    title: str
    description: str | None = None
    success_description: str | None = None
    due_on: date | None = None
    weight: float | None = None
    position: int = 0
    status: QuestStatus = QuestStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Milestone(SQLModel, table=True):
    __tablename__ = "milestone"

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(foreign_key="goal.id", ondelete="RESTRICT", index=True)
    title: str
    description: str | None = None
    due_on: date | None = None
    weight: float | None = None
    position: int = 0
    status: QuestStatus = QuestStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class SideQuest(SQLModel, table=True):
    __tablename__ = "side_quest"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    due_on: date | None = None
    position: int = 0
    status: QuestStatus = QuestStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Chapter(SQLModel, table=True):
    __tablename__ = "chapter"
    __table_args__ = (
        CheckConstraint(
            "(milestone_id IS NULL) <> (side_quest_id IS NULL)",
            name="ck_chapter_one_parent",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    milestone_id: int | None = Field(
        default=None, foreign_key="milestone.id", ondelete="RESTRICT", index=True
    )
    side_quest_id: int | None = Field(
        default=None, foreign_key="side_quest.id", ondelete="RESTRICT", index=True
    )
    title: str
    description: str | None = None
    weight: float | None = None
    position: int = 0
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Task(SQLModel, table=True):
    __tablename__ = "task"
    __table_args__ = (
        CheckConstraint(
            "(ambition_id IS NOT NULL) + (goal_id IS NOT NULL) + (milestone_id IS NOT NULL)"
            " + (chapter_id IS NOT NULL) + (side_quest_id IS NOT NULL) <= 1",
            name="ck_task_at_most_one_parent",
        ),
        CheckConstraint(
            "(ambition_id IS NULL AND goal_id IS NULL AND milestone_id IS NULL"
            " AND chapter_id IS NULL AND side_quest_id IS NULL) OR organized_at IS NOT NULL",
            name="ck_task_parent_is_organized",
        ),
        CheckConstraint(
            f"(status = '{_TASK_COMPLETED}') = (completed_at IS NOT NULL)",
            name="ck_task_completed_at",
        ),
        CheckConstraint(
            "estimate_minutes IS NULL OR estimate_minutes > 0",
            name="ck_task_estimate_positive",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.NORMAL
    estimate_minutes: int | None = None
    due_on: date | None = None
    weight: float | None = None
    position: int = 0
    ambition_id: int | None = Field(
        default=None, foreign_key="ambition.id", ondelete="RESTRICT", index=True
    )
    goal_id: int | None = Field(
        default=None, foreign_key="goal.id", ondelete="RESTRICT", index=True
    )
    milestone_id: int | None = Field(
        default=None, foreign_key="milestone.id", ondelete="RESTRICT", index=True
    )
    chapter_id: int | None = Field(
        default=None, foreign_key="chapter.id", ondelete="RESTRICT", index=True
    )
    side_quest_id: int | None = Field(
        default=None, foreign_key="side_quest.id", ondelete="RESTRICT", index=True
    )
    organized_at: datetime | None = Field(default=None, index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class TimeBlock(SQLModel, table=True):
    __tablename__ = "time_block"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_time_block_end_after_start"),
        Index(
            "ux_time_block_provider_external_event",
            "provider",
            "external_event_id",
            unique=True,
            sqlite_where=text("external_event_id IS NOT NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id", ondelete="RESTRICT", index=True)
    start_at: datetime = Field(index=True)
    end_at: datetime
    status: TimeBlockStatus = TimeBlockStatus.SCHEDULED
    provider: TimeBlockProvider = TimeBlockProvider.INTERNAL
    external_event_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class SchemaVersion(SQLModel, table=True):
    __tablename__ = "schema_version"

    id: int = Field(default=1, primary_key=True)
    version: int
