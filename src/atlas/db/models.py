from datetime import UTC, date, datetime

from sqlalchemy import JSON, Column, Index
from sqlmodel import Field, SQLModel

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    Source,
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
    area_id: int = Field(foreign_key="area.id")
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
    status: GoalStatus = GoalStatus.ACTIVE
    achieved_at: datetime | None = None


class Milestone(SQLModel, table=True):
    __tablename__ = "milestone"

    id: int | None = Field(default=None, primary_key=True)
    goal_id: int = Field(foreign_key="goal.id")
    name: str
    due_on: date | None = None
    done_at: datetime | None = None


class SchemaVersion(SQLModel, table=True):
    __tablename__ = "schema_version"

    id: int = Field(default=1, primary_key=True)
    version: int
