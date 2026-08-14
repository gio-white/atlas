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


class GoalKind(StrEnum):
    METRIC_TARGET = "metric_target"
    MILESTONE = "milestone"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class Measure(StrEnum):
    LATEST_VALUE = "latest_value"
    CUMULATIVE_SINCE_START = "cumulative_since_start"


class Source(StrEnum):
    CLI = "cli"
    API = "api"
    IMPORT = "import"


class PaceStatus(StrEnum):
    ACHIEVED = "achieved"
    OVERDUE = "overdue"
    NO_DATA = "no_data"
    AHEAD = "ahead"
    ON_TRACK = "on_track"
    BEHIND = "behind"


class ScreenJudgment(StrEnum):
    USEFUL = "useful"
    WASTE = "waste"
    NEUTRAL = "neutral"


class ScreenBudgetTargetKind(StrEnum):
    JUDGMENT = "judgment"
    CATEGORY = "category"
