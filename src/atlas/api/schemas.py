from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    HabitApply,
    HabitCheck,
    HabitFrequency,
    HabitMarkResult,
    HabitSource,
    HabitThreshold,
    LibraryKind,
    LibraryStatus,
    MetricOrigin,
    Period,
    ScreenBudgetTargetKind,
    ScreenInsightKind,
    ScreenJudgment,
    ScreenScoreBand,
    SleepStage,
    Source,
    TimeOfDay,
    ValueType,
)
from atlas.domain.habits import DayReason, DayStatus, PeriodState


class MetricCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = None
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
    origin: MetricOrigin
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


class HabitRuleIn(BaseModel):
    """A habit's rule (habits brief §2). A manual rule has no data fields; a data rule names a
    source, and a missing threshold or value takes the source's default."""

    model_config = ConfigDict(extra="forbid")

    frequency: HabitFrequency
    check: HabitCheck = HabitCheck.MANUAL
    weekdays: list[int] | None = None
    times: int | None = None
    source: HabitSource | None = None
    source_ref: str | None = None
    threshold: HabitThreshold | None = None
    value: float | None = None


class HabitRuleOut(BaseModel):
    starts_on: date
    frequency: HabitFrequency
    check: HabitCheck
    weekdays: list[int] | None
    times: int | None
    source: HabitSource | None
    source_ref: str | None
    source_ref_name: str | None
    threshold: HabitThreshold | None
    value: float | None


class HabitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    slug: str | None = None
    time_of_day: TimeOfDay = TimeOfDay.ANYTIME
    first_day: date | None = None
    rule: HabitRuleIn


class HabitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    time_of_day: TimeOfDay | None = None
    rule: HabitRuleIn | None = None
    apply: HabitApply = HabitApply.FROM_TODAY


class HabitOut(BaseModel):
    id: int
    slug: str
    name: str
    time_of_day: TimeOfDay
    first_day: date
    archived_at: datetime | None
    rule: HabitRuleOut
    """The rule in force today."""


class HabitDaySet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: HabitMarkResult


class HabitDayOut(BaseModel):
    day: date
    result: HabitMarkResult | None
    """What you set for the day; empty when nothing is stored (a manual day without a tick)."""


class HabitFreezeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    habit: str | None = None
    """The habit's slug; empty freezes every habit."""
    start_on: date | None = None
    end_on: date | None = None
    reason: str | None = None


class HabitFreezeOut(BaseModel):
    id: int
    habit: str | None
    start_on: date
    end_on: date
    reason: str | None
    created_at: datetime


class WeekSoFarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    sessions_kept: int
    sessions_total: int
    habits_kept: int
    habits_judged: int
    habits_kept_share: float | None
    sleep_average_minutes: float | None
    sleep_nights: int
    screen_score: int | None


class WeekNumbersOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    sessions_kept: int
    sessions_total: int
    tasks_completed: int
    milestones_completed: int
    habits_kept: int
    habits_judged: int
    habits_kept_share: float | None
    sleep_average_minutes: float | None
    sleep_average_bedtime: float | None
    sleep_average_wake: float | None
    sleep_nights: int
    sleep_missing_nights: int
    screen_total: float | None
    screen_daily_average: float | None
    screen_score: int | None
    screen_good: float | None
    screen_neutral: float | None
    screen_bad: float | None
    titles_finished: int


class HabitDayResultOut(BaseModel):
    """One day of one habit (habits brief §6). `value` is the data habit's reading: minutes, or
    a time of day in minutes after midnight (negative for a session planned the day before)."""

    model_config = ConfigDict(from_attributes=True)

    day: date
    status: DayStatus
    reason: DayReason | None
    value: float | None


class HabitStreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    count: int
    period: Period


class HabitProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: Period
    done: int
    target: int


class HabitKeptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    done: int
    target: int
    share: float | None


class HabitDayRowOut(BaseModel):
    habit: HabitOut
    result: HabitDayResultOut
    streak: HabitStreakOut
    progress: HabitProgressOut | None


class HabitDayCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    done: int
    total: int


class HabitsDayOut(BaseModel):
    day: date
    done: int
    total: int
    week: list[HabitDayCountOut]
    rows: list[HabitDayRowOut]


class HabitWeekRowOut(BaseModel):
    habit: HabitOut
    days: list[HabitDayResultOut]
    streak: HabitStreakOut
    progress: HabitProgressOut | None


class HabitsWeekOut(BaseModel):
    as_of: date
    week_start: date
    week_end: date
    rows: list[HabitWeekRowOut]
    kept: HabitKeptOut
    kept_last_week: HabitKeptOut


class HabitPeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: Period
    start: date
    end: date
    target: int
    done: int
    state: PeriodState


class HabitDetailOut(BaseModel):
    habit: HabitOut
    as_of: date
    current_streak: HabitStreakOut
    best_streak: int
    kept_last_4_weeks: HabitKeptOut
    history: list[HabitPeriodOut]
    recent: list[HabitDayResultOut]
    freezes: list[HabitFreezeOut]


class WeekHabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    done: int
    target: int


class ThisWeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    week_start: date
    week_end: date
    complete: bool
    current: WeekNumbersOut
    previous: WeekNumbersOut
    habits: list[WeekHabitOut]


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
    target_slug: str = "all"
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
    complete_through: datetime | None = None


class ScreenDeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    complete_through: datetime | None = None


class ScreenDeviceOut(BaseModel):
    id: int
    slug: str
    name: str
    complete_through: datetime | None
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
    last_recorded_at: datetime | None


class JournalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    occurred_on: date | None = None


class JournalDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    text: str | None
    entry_id: int | None


class LibraryTopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str | None = None


class LibraryTopicUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None


class LibraryTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    archived_at: datetime | None


class LibraryTopicRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class LibraryTitleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    kind: LibraryKind
    name: str | None = None
    creator: str | None = None
    recommended_by: str | None = None
    status: LibraryStatus = LibraryStatus.QUEUED
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    rating: int | None = None
    link: str | None = None
    topics: list[str] = Field(default_factory=list)
    image_url: str | None = None


class LibraryTitleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    kind: LibraryKind | None = None
    creator: str | None = None
    recommended_by: str | None = None
    status: LibraryStatus | None = None
    started_on: date | None = None
    finished_on: date | None = None
    progress: str | None = None
    note: str | None = None
    rating: int | None = None
    link: str | None = None
    topics: list[str] | None = None
    image_url: str | None = None


class LibraryTitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    kind: LibraryKind
    creator: str | None
    recommended_by: str | None
    status: LibraryStatus
    started_on: date | None
    finished_on: date | None
    progress: str | None
    note: str | None
    rating: int | None
    link: str | None
    topics: list[LibraryTopicRefOut]
    image: str | None
    created_at: datetime | None


class LibraryLinkLookupIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str


class LibraryLinkSuggestionOut(BaseModel):
    link: str
    name: str | None
    kind: LibraryKind | None
    creator: str | None
    image_url: str | None
    existing: str | None


class LibraryTitleFromLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    kind: LibraryKind | None = None
    status: LibraryStatus = LibraryStatus.QUEUED
    topics: list[str] = Field(default_factory=list)
    note: str | None = None


class LibraryKindCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: LibraryKind
    count: int
    share: float


class LibraryTopicCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    count: int
    share: float


class LibraryShelvesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    queued: list[LibraryTitleOut]
    in_progress: list[LibraryTitleOut]
    done: list[LibraryTitleOut]
    dropped: list[LibraryTitleOut]


class LibraryDashboardOut(BaseModel):
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
    by_kind: list[LibraryKindCountOut]
    by_topic: list[LibraryTopicCountOut]
    recently_finished: list[LibraryTitleOut]
    library: LibraryShelvesOut


class SleepStageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: SleepStage
    started_at: datetime
    ended_at: datetime


class SleepSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    ended_at: datetime
    stages: list[SleepStageIn] = Field(default_factory=list)
    note: str | None = None


class SleepStageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage: SleepStage
    started_at: datetime
    ended_at: datetime


class SleepSessionOut(BaseModel):
    id: int
    started_at: datetime
    ended_at: datetime
    occurred_on: date
    note: str | None
    source: Source
    created_at: datetime
    stages: list[SleepStageOut]


class SleepStageMinutesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    awake: float
    rem: float
    light: float
    deep: float


class SleepSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage: SleepStage
    start_offset: float
    end_offset: float


class SleepNightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    session_id: int | None
    started_at: datetime
    ended_at: datetime
    bed_offset: float
    wake_offset: float
    in_bed_minutes: float
    asleep_minutes: float
    stages: SleepStageMinutesOut
    segments: list[SleepSegmentOut]


class SleepDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    night: SleepNightOut | None


class SleepViewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    as_of: date
    range_start: date
    range_end: date
    night: SleepNightOut | None
    days: list[SleepDayOut]
    nights_logged: int
    average_asleep: float | None
    average_bed_offset: float | None
    average_wake_offset: float | None
    average_stages: SleepStageMinutesOut | None
    bed_spread: float | None
    wake_spread: float | None
    last_recorded_at: datetime | None


class ImportSummaryOut(BaseModel):
    schema_version: int
    ignored_sections: list[str]
    notes: list[str]
