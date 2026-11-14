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


class HabitKind(StrEnum):
    CHECK = "check"
    COUNT = "count"
    DURATION = "duration"
    QUIT = "quit"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANYTIME = "anytime"


class EntertainmentKind(StrEnum):
    FILM = "film"
    SERIES = "series"
    ANIME = "anime"
    VIDEO = "video"
    PODCAST = "podcast"
    BOOK = "book"
    MUSIC = "music"
    OTHER = "other"


class EntertainmentStatus(StrEnum):
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


class TimeBlockProvider(StrEnum):
    INTERNAL = "internal"


class ParentKind(StrEnum):
    """The kind of quest item a task (or another item) hangs under."""

    AMBITION = "ambition"
    GOAL = "goal"
    MILESTONE = "milestone"
    CHAPTER = "chapter"
    SIDE_QUEST = "side_quest"
