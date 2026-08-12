from dataclasses import dataclass
from datetime import UTC, date, datetime

from atlas.domain.enums import Aggregation, Comparator, GoalKind, Measure, Period

_MIN = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class EntryView:
    occurred_on: date
    value_num: float | None = None
    value_bool: bool | None = None
    value_text: str | None = None
    occurred_at: datetime | None = None
    created_at: datetime | None = None
    id: int | None = None

    def numeric_value(self) -> float | None:
        if self.value_num is not None:
            return self.value_num
        if self.value_bool is not None:
            return 1.0 if self.value_bool else 0.0
        return None

    def recency_key(self) -> tuple[date, datetime, datetime, int]:
        return (
            self.occurred_on,
            _as_aware(self.occurred_at),
            _as_aware(self.created_at),
            self.id or 0,
        )


@dataclass(frozen=True, slots=True)
class HabitSpec:
    period: Period
    target_value: float
    comparator: Comparator
    aggregation: Aggregation
    active_from: date
    active_to: date | None = None
    weekdays: frozenset[int] | None = None

    def __post_init__(self) -> None:
        if self.weekdays is not None and not isinstance(self.weekdays, frozenset):
            object.__setattr__(self, "weekdays", frozenset(self.weekdays))


@dataclass(frozen=True, slots=True)
class GoalSpec:
    kind: GoalKind
    start_on: date
    due_on: date
    target_value: float | None = None
    comparator: Comparator | None = None
    baseline_value: float | None = None
    measure: Measure | None = None


@dataclass(frozen=True, slots=True)
class MilestoneView:
    name: str
    due_on: date | None = None
    done_at: datetime | None = None

    @property
    def is_done(self) -> bool:
        return self.done_at is not None


@dataclass(frozen=True, slots=True)
class Bucket:
    period: Period
    key: date | tuple[int, int]
    start: date
    end: date

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end

    def is_complete(self, as_of: date) -> bool:
        return self.end < as_of

    def is_in_progress(self, as_of: date) -> bool:
        return self.start <= as_of <= self.end


@dataclass(frozen=True, slots=True)
class GoalProgress:
    current: float | None
    baseline: float | None
    fraction: float | None
    target_met: bool


def _as_aware(value: datetime | None) -> datetime:
    if value is None:
        return _MIN
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
