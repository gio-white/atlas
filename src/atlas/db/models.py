from datetime import UTC, date, datetime

from sqlalchemy import JSON, Column, Index, LargeBinary
from sqlmodel import Field, SQLModel

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    EntertainmentKind,
    EntertainmentStatus,
    GoalHorizon,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    ScreenBudgetTargetKind,
    ScreenJudgment,
    Source,
    TaskBucket,
    TaskPriority,
    ValueType,
)


class Area(SQLModel, table=True):
    __tablename__ = "area"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    description: str | None = None
    archived_at: datetime | None = None


class Metric(SQLModel, table=True):
    __tablename__ = "metric"

    id: int | None = Field(default=None, primary_key=True)
    area_id: int = Field(foreign_key="area.id")
    slug: str = Field(unique=True, index=True)
    name: str
    value_type: ValueType
    unit: str | None = None
    aggregation: Aggregation
    direction: Direction
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


class Goal(SQLModel, table=True):
    __tablename__ = "goal"

    id: int | None = Field(default=None, primary_key=True)
    area_id: int | None = Field(default=None, foreign_key="area.id")
    slug: str = Field(unique=True, index=True)
    name: str
    kind: GoalKind
    metric_id: int | None = Field(default=None, foreign_key="metric.id")
    target_value: float | None = None
    comparator: Comparator | None = None
    baseline_value: float | None = None
    measure: Measure | None = None
    start_on: date
    due_on: date
    horizon: GoalHorizon = GoalHorizon.LONG
    parent_id: int | None = Field(default=None, foreign_key="goal.id")
    description: str | None = None
    status: GoalStatus = GoalStatus.ACTIVE
    achieved_at: datetime | None = None


class Milestone(SQLModel, table=True):
    __tablename__ = "milestone"

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(foreign_key="goal.id")
    name: str
    due_on: date | None = None
    done_at: datetime | None = None


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


class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    bucket: TaskBucket
    due_on: date | None = None
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    goal_id: int | None = Field(default=None, foreign_key="goal.id")
    done_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EntertainmentTopic(SQLModel, table=True):
    __tablename__ = "entertainment_topic"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    archived_at: datetime | None = None


class EntertainmentTitle(SQLModel, table=True):
    __tablename__ = "entertainment_title"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    kind: EntertainmentKind
    creator: str | None = None
    recommended_by: str | None = None
    status: EntertainmentStatus = EntertainmentStatus.QUEUED
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    image_url: str | None = None
    image_bytes: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    image_media_type: str | None = None
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EntertainmentTitleTopic(SQLModel, table=True):
    __tablename__ = "entertainment_title_topic"

    title_id: int = Field(foreign_key="entertainment_title.id", primary_key=True)
    topic_id: int = Field(foreign_key="entertainment_topic.id", primary_key=True)


class SchemaVersion(SQLModel, table=True):
    __tablename__ = "schema_version"

    id: int = Field(default=1, primary_key=True)
    version: int
