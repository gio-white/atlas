from enum import StrEnum


class ValueType(StrEnum):
    BOOL = "bool"
    COUNT = "count"
    QUANTITY = "quantity"
    DURATION = "duration"
    RATING = "rating"
    TEXT = "text"


class Aggregation(StrEnum):
    SUM = "sum"
    LAST = "last"
    MEAN = "mean"
    MAX = "max"
    MIN = "min"


class Direction(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


class Period(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class Comparator(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    EXACTLY = "exactly"


class MetricOrigin(StrEnum):
    """How a metric came to exist. Only `manual` ones are set up by hand."""

    MANUAL = "manual"
    HABIT = "habit"
    SCREEN = "screen"
    JOURNAL = "journal"


AUTOMATIC_METRIC_ORIGINS = frozenset({MetricOrigin.SCREEN})
"""Origins whose entries are written by device data, never typed."""


class Source(StrEnum):
    CLI = "cli"
    API = "api"
    IMPORT = "import"


class ScreenJudgment(StrEnum):
    USEFUL = "useful"
    WASTE = "waste"
    NEUTRAL = "neutral"


class ScreenBudgetTargetKind(StrEnum):
    JUDGMENT = "judgment"
    CATEGORY = "category"
    TOTAL = "total"
    """All screen time, whatever the app. Its `target_slug` is always `all`."""


class ScreenScoreBand(StrEnum):
    GOOD = "good"
    OK = "ok"
    POOR = "poor"


class ScreenInsightKind(StrEnum):
    WEEKEND_SPIKE = "weekend_spike"
    WASTE_SHARE = "waste_share"
    LATE_NIGHT = "late_night"
    IMPROVING = "improving"
    SEQUENCE = "sequence"
    BUDGET = "budget"


class HabitFrequency(StrEnum):
    """How often a habit is due (habits brief §5). Weeks run Monday to Sunday."""

    EVERY_DAY = "every_day"
    SPECIFIC_DAYS = "specific_days"
    TIMES_A_WEEK = "times_a_week"
    TIMES_A_MONTH = "times_a_month"


class HabitCheck(StrEnum):
    """How a habit is checked: you tick it (`manual`) or Atlas reads your data (`data`)."""

    MANUAL = "manual"
    DATA = "data"


class HabitSource(StrEnum):
    """Where a data habit reads its day's value. The registry is `habit_sources.SOURCES`."""

    WAKE_TIME = "wake_time"
    BEDTIME = "bedtime"
    TIME_ASLEEP = "time_asleep"
    SCREEN_BAD_APPS = "screen_bad_apps"
    SCREEN_CATEGORY = "screen_category"
    SCREEN_APP = "screen_app"
    SCREEN_TOTAL = "screen_total"
    SESSIONS_PLANNED = "sessions_planned"


class HabitThreshold(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    BEFORE = "before"
    AFTER = "after"


class HabitApply(StrEnum):
    """Where a rule change applies: from today, or to every day since the habit's first."""

    FROM_TODAY = "from_today"
    ALL_DAYS = "all_days"


class HabitMarkResult(StrEnum):
    """An answer you gave for a day: a tick, or "Set by you" on a data habit."""

    DONE = "done"
    NOT_DONE = "not_done"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANYTIME = "anytime"


class LibraryKind(StrEnum):
    FILM = "film"
    SERIES = "series"
    ANIME = "anime"
    VIDEO = "video"
    PODCAST = "podcast"
    BOOK = "book"
    MUSIC = "music"
    OTHER = "other"


class LibraryStatus(StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DROPPED = "dropped"


class SleepStage(StrEnum):
    AWAKE = "awake"
    REM = "rem"
    LIGHT = "light"
    DEEP = "deep"


class QuestStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class ChapterState(StrEnum):
    EMPTY = "empty"
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TimeBlockStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"
    """The session's time came and it did not happen (shown as "Didn't happen"). Unlike
    `cancelled`, which is called off ahead of time, it still counts against "Sessions kept"."""


class TimeBlockProvider(StrEnum):
    INTERNAL = "internal"


class ParentKind(StrEnum):
    """The kind of quest item a task (or another item) hangs under."""

    AMBITION = "ambition"
    GOAL = "goal"
    MILESTONE = "milestone"
    CHAPTER = "chapter"
    SIDE_QUEST = "side_quest"
