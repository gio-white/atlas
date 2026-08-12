from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    GoalKind,
    GoalStatus,
    Measure,
    PaceStatus,
    Period,
    Source,
    ValueType,
)


class AreaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str | None = None
    description: str | None = None


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None
    archived_at: datetime | None


class MetricCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    area: str
    value_type: ValueType
    aggregation: Aggregation
    name: str | None = None
    unit: str | None = None
    direction: Direction = Direction.NEUTRAL


class MetricOut(BaseModel):
    id: int
    slug: str
    area: str
    name: str
    value_type: ValueType
    unit: str | None
    aggregation: Aggregation
    direction: Direction
    archived_at: datetime | None


class EntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    value: bool | float | str | None = None
    occurred_on: date | None = None
    occurred_at: datetime | None = None
    note: str | None = None


class EntryAmend(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: bool | float | str | None = None
    occurred_on: date | None = None
    occurred_at: datetime | None = None
    note: str | None = None


class EntryOut(BaseModel):
    id: int
    metric: str
    occurred_on: date
    occurred_at: datetime | None
    value_num: float | None
    value_bool: bool | None
    value_text: str | None
    note: str | None
    source: Source
    created_at: datetime


class HabitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    metric: str
    period: Period
    target_value: float
    comparator: Comparator
    name: str | None = None
    weekdays: list[int] | None = None
    active_from: date | None = None
    active_to: date | None = None


class HabitOut(BaseModel):
    id: int
    slug: str
    metric: str
    name: str
    period: Period
    target_value: float
    comparator: Comparator
    weekdays: list[int] | None
    active_from: date
    active_to: date | None


class MilestoneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    due_on: date | None = None


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    area: str
    kind: GoalKind
    start_on: date
    due_on: date
    name: str | None = None
    metric: str | None = None
    target_value: float | None = None
    comparator: Comparator | None = None
    baseline_value: float | None = None
    measure: Measure | None = None
    milestones: list[MilestoneCreate] | None = None


class GoalOut(BaseModel):
    id: int
    slug: str
    area: str
    name: str
    kind: GoalKind
    metric: str | None
    target_value: float | None
    comparator: Comparator | None
    baseline_value: float | None
    measure: Measure | None
    start_on: date
    due_on: date
    status: GoalStatus
    achieved_at: datetime | None


class HabitStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    metric_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_streak: int
    longest_streak: int
    adherence: float | None
    current_value: float | None
    satisfied: bool
    scheduled: bool
    as_of: date


class GoalProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    kind: GoalKind
    status: GoalStatus
    metric_slug: str | None
    current: float | None
    baseline: float | None
    fraction: float | None
    target_met: bool
    pace: PaceStatus
    target_value: float | None
    start_on: date
    due_on: date
    as_of: date


class LoggedEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metric_slug: str
    occurred_on: date
    value_num: float | None
    value_bool: bool | None
    value_text: str | None
    note: str | None


class TodayViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    habits: list[HabitStatusOut]
    entries: list[LoggedEntryOut]
    goals: list[GoalProgressOut]


class WeekDayCellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    scheduled: bool
    value: float | None
    satisfied: bool | None


class WeekHabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    metric_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_value: float | None
    satisfied: bool
    current_streak: int
    days: list[WeekDayCellOut]


class WeekViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    week_end: date
    habits: list[WeekHabitOut]


class MetricSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    unit: str | None
    aggregation: Aggregation
    latest_on: date | None
    latest_value: float | None


class AreaViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str | None
    as_of: date
    metrics: list[MetricSnapshotOut]
    habits: list[HabitStatusOut]
    goals: list[GoalProgressOut]
