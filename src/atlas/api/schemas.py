from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

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
    PaceStatus,
    Period,
    ScreenBudgetTargetKind,
    ScreenInsightKind,
    ScreenJudgment,
    ScreenScoreBand,
    Source,
    TaskBucket,
    TaskPriority,
    ValueType,
)


class AreaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str | None = None
    description: str | None = None


class AreaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class MetricUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    unit: str | None = None
    direction: Direction | None = None


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


class HabitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    target_value: float | None = None
    comparator: Comparator | None = None
    weekdays: list[int] | None = None
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
    area: str | None = None
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
    horizon: GoalHorizon | None = None
    parent: str | None = None
    description: str | None = None


class GoalOut(BaseModel):
    id: int
    slug: str
    area: str | None
    name: str
    kind: GoalKind
    metric: str | None
    target_value: float | None
    comparator: Comparator | None
    baseline_value: float | None
    measure: Measure | None
    start_on: date
    due_on: date
    horizon: GoalHorizon
    parent: str | None
    description: str | None
    status: GoalStatus
    achieved_at: datetime | None


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    due_on: date | None = None
    target_value: float | None = None
    status: GoalStatus | None = None
    horizon: GoalHorizon | None = None
    parent: str | None = None
    description: str | None = None
    area: str | None = None


class MilestoneOut(BaseModel):
    name: str
    due_on: date | None
    done_at: datetime | None


class GoalDetailOut(GoalOut):
    milestones: list[MilestoneOut]


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
    horizon: GoalHorizon
    parent: str | None
    description: str | None


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


class HabitsCalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    period: Period
    range_start: date
    range_end: date
    habits: list[WeekHabitOut]


class HomeWeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    week_end: date
    updates: float
    updates_last_week: float
    updates_delta: float | None
    slips: float
    slips_last_week: float
    slips_delta: float | None
    focus_minutes: float
    focus_minutes_last_week: float
    focus_delta: float | None
    tasks_done: float
    tasks_done_last_week: float
    tasks_delta: float | None
    series_updates: list[float]
    series_slips: list[float]


class GoalBoardColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    horizon: GoalHorizon
    on_track: int
    total: int
    fraction: float | None
    goals: list[GoalProgressOut]


class GoalBoardTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    bucket: TaskBucket
    due_on: date | None
    due_at: datetime | None
    priority: TaskPriority
    done_at: datetime | None
    created_at: datetime
    goal: str | None


class GoalBoardWeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    done: int
    fraction: float | None
    tasks: list[GoalBoardTaskOut]


class GoalsBoardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    long: GoalBoardColumnOut
    medium: GoalBoardColumnOut
    short: GoalBoardColumnOut
    week: GoalBoardWeekOut


class HabitsBoardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    scheduled: int
    satisfied: int
    fraction: float | None
    day: list[HabitStatusOut]
    week: list[HabitStatusOut]
    month: list[HabitStatusOut]


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


class ScreenCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    judgment: ScreenJudgment
    name: str | None = None


class ScreenCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    judgment: ScreenJudgment | None = None


class ScreenCategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    judgment: ScreenJudgment
    archived_at: datetime | None


class ScreenAppCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    category: str
    name: str | None = None


class ScreenAppUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    category: str | None = None


class ScreenAppOut(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    metric: str
    archived_at: datetime | None


class ScreenBudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    target_kind: ScreenBudgetTargetKind
    target_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    name: str | None = None
    active_from: date | None = None
    active_to: date | None = None


class ScreenBudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    target_kind: ScreenBudgetTargetKind | None = None
    target_slug: str | None = None
    target_value: float | None = None
    comparator: Comparator | None = None
    active_to: date | None = None


class ScreenBudgetOut(BaseModel):
    id: int
    slug: str
    name: str
    target_kind: ScreenBudgetTargetKind
    target_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    active_from: date
    active_to: date | None


class ScreenAppRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    category: str
    metric: str
    minutes: float | None
    archived_at: datetime | None


class ScreenCategoryRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    judgment: ScreenJudgment
    minutes: float | None
    apps: list[ScreenAppRowOut]
    archived_at: datetime | None


class ScreenJudgmentTotalsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    useful: float | None
    waste: float | None
    neutral: float | None
    total: float | None


class ScreenSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app: str
    category: str
    metric: str
    occurred_on: date
    minutes: float | None
    note: str | None


class ScreenDeviceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str | None = None


class ScreenDeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None


class ScreenDeviceOut(BaseModel):
    id: int
    slug: str
    name: str
    archived_at: datetime | None


class ScreenSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: str
    minutes: float | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    occurred_on: date | None = None
    device: str | None = None
    note: str | None = None


class ScreenSessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minutes: float | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    occurred_on: date | None = None
    device: str | None = None
    note: str | None = None


class ScreenSessionRecordOut(BaseModel):
    id: int
    app: str
    device: str | None
    started_at: datetime | None
    ended_at: datetime | None
    minutes: float
    occurred_on: date
    note: str | None
    source: Source
    created_at: datetime
    entry_id: int | None


class ScreenBudgetStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    target_kind: ScreenBudgetTargetKind
    target_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_value: float | None
    satisfied: bool
    scheduled: bool
    current_streak: int
    longest_streak: int
    adherence: float | None
    as_of: date


class ScreenViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    categories: list[ScreenCategoryRowOut]
    judgments: ScreenJudgmentTotalsOut
    sessions: list[ScreenSessionOut]
    budgets: list[ScreenBudgetStatusOut]


class ScreenAppShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    category: str
    category_name: str
    judgment: ScreenJudgment
    minutes: float
    share: float


class ScreenCategoryShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    judgment: ScreenJudgment
    minutes: float
    share: float
    apps: list[ScreenAppShareOut]


class ScreenDeviceShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    minutes: float
    share: float


class ScreenDayBarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    useful: float
    waste: float
    neutral: float
    total: float


class ScreenComparisonPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current: float
    previous: float


class ScreenTrendPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start: date
    daily_average: float | None


class ScreenLongestDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    minutes: float


class ScreenInsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: ScreenInsightKind
    summary: str
    prescription: str


class ScreenDashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: Period
    as_of: date
    range_start: date
    range_end: date
    previous_start: date
    previous_end: date
    total: float | None
    daily_average: float | None
    longest_day: ScreenLongestDayOut | None
    delta_minutes: float | None
    delta_fraction: float | None
    score: int | None
    score_band: ScreenScoreBand | None
    judgments: ScreenJudgmentTotalsOut
    apps: list[ScreenAppShareOut]
    categories: list[ScreenCategoryShareOut]
    devices: list[ScreenDeviceShareOut]
    daily: list[ScreenDayBarOut]
    comparison: list[ScreenComparisonPointOut]
    hours: list[list[float]]
    trend: list[ScreenTrendPointOut]
    insights: list[ScreenInsightOut]
    budgets: list[ScreenBudgetStatusOut]


class UpdateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_on: date | None = None
    note: str | None = None


class UpdatesStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    checked_in: bool
    current_streak: int
    longest_streak: int


class SlipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_on: date | None = None
    note: str | None = None


class SlipsWeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    week_end: date
    this_week: float
    last_week: float
    delta_fraction: float | None
    series: list[float]


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    bucket: TaskBucket = TaskBucket.TODAY
    due_on: date | None = None
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.NORMAL
    goal: str | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    bucket: TaskBucket | None = None
    due_on: date | None = None
    due_at: datetime | None = None
    priority: TaskPriority | None = None
    done: bool | None = None
    goal: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    bucket: TaskBucket
    due_on: date | None
    due_at: datetime | None
    priority: TaskPriority
    goal: str | None
    done_at: datetime | None
    created_at: datetime


class JournalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    occurred_on: date | None = None


class JournalDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    text: str | None
    entry_id: int | None


class EntertainmentTopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str | None = None


class EntertainmentTopicUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None


class EntertainmentTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    archived_at: datetime | None


class EntertainmentTopicRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class EntertainmentTitleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    kind: EntertainmentKind
    name: str | None = None
    creator: str | None = None
    recommended_by: str | None = None
    status: EntertainmentStatus = EntertainmentStatus.QUEUED
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    topics: list[str] = Field(default_factory=list)
    image_url: str | None = None


class EntertainmentTitleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    kind: EntertainmentKind | None = None
    creator: str | None = None
    recommended_by: str | None = None
    status: EntertainmentStatus | None = None
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    topics: list[str] | None = None
    image_url: str | None = None


class EntertainmentTitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    kind: EntertainmentKind
    creator: str | None
    recommended_by: str | None
    status: EntertainmentStatus
    started_on: date | None
    finished_on: date | None
    progress: str | None
    note: str | None
    topics: list[EntertainmentTopicRefOut]
    image: str | None


class EntertainmentKindCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: EntertainmentKind
    count: int
    share: float


class EntertainmentTopicCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    count: int
    share: float


class EntertainmentLibraryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    queued: list[EntertainmentTitleOut]
    in_progress: list[EntertainmentTitleOut]
    done: list[EntertainmentTitleOut]
    dropped: list[EntertainmentTitleOut]


class EntertainmentViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    in_progress: int
    finished_this_week: int
    last_finished: EntertainmentTitleOut | None


class EntertainmentDashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: Period
    as_of: date
    range_start: date
    range_end: date
    finished_in_range: int
    started_in_range: int
    queued: int
    in_progress: int
    done: int
    dropped: int
    by_kind: list[EntertainmentKindCountOut]
    by_topic: list[EntertainmentTopicCountOut]
    recently_finished: list[EntertainmentTitleOut]
    library: EntertainmentLibraryOut
