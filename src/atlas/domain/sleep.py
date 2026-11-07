from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, tzinfo

from atlas.domain.enums import SleepStage

SLEEP_WINDOW_DAYS = 7


@dataclass(frozen=True, slots=True)
class SleepStageSpan:
    stage: SleepStage
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True, slots=True)
class SleepSessionSpec:
    started_at: datetime
    ended_at: datetime
    occurred_on: date
    minutes: float
    stages: tuple[SleepStageSpan, ...]


@dataclass(frozen=True, slots=True)
class SleepSessionView:
    id: int | None
    started_at: datetime
    ended_at: datetime
    occurred_on: date
    stages: tuple[SleepStageSpan, ...]
    note: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SleepStageMinutes:
    awake: float
    rem: float
    light: float
    deep: float


@dataclass(frozen=True, slots=True)
class SleepSegment:
    stage: SleepStage
    start_offset: float
    end_offset: float


@dataclass(frozen=True, slots=True)
class SleepNight:
    date: date
    session_id: int | None
    started_at: datetime
    ended_at: datetime
    bed_offset: float
    wake_offset: float
    in_bed_minutes: float
    asleep_minutes: float
    stages: SleepStageMinutes
    segments: tuple[SleepSegment, ...]


@dataclass(frozen=True, slots=True)
class SleepDay:
    date: date
    night: SleepNight | None


@dataclass(frozen=True, slots=True)
class SleepWeekMath:
    as_of: date
    range_start: date
    range_end: date
    night: SleepNight | None
    days: tuple[SleepDay, ...]
    nights_logged: int
    average_asleep: float | None
    average_bed_offset: float | None
    average_wake_offset: float | None
    average_stages: SleepStageMinutes | None
    bed_spread: float | None
    wake_spread: float | None
    last_recorded_at: datetime | None


def resolve_sleep_session(
    *,
    started_at: datetime,
    ended_at: datetime,
    stages: Sequence[SleepStageSpan],
    timezone: tzinfo,
) -> SleepSessionSpec:
    start = _as_utc(started_at)
    end = _as_utc(ended_at)
    if end <= start:
        raise ValueError("ended_at must be after started_at")
    spans = sorted(
        (
            SleepStageSpan(
                stage=SleepStage(span.stage),
                started_at=_as_utc(span.started_at),
                ended_at=_as_utc(span.ended_at),
            )
            for span in stages
        ),
        key=lambda span: span.started_at,
    )
    previous_end: datetime | None = None
    for span in spans:
        if span.ended_at <= span.started_at:
            raise ValueError("each stage must end after it starts")
        if span.started_at < start or span.ended_at > end:
            raise ValueError("stages must fall inside the session")
        if previous_end is not None and span.started_at < previous_end:
            raise ValueError("stages must not overlap")
        previous_end = span.ended_at
    return SleepSessionSpec(
        started_at=start,
        ended_at=end,
        occurred_on=end.astimezone(timezone).date(),
        minutes=_minutes(start, end),
        stages=tuple(spans),
    )


def sleep_night(view: SleepSessionView, timezone: tzinfo) -> SleepNight:
    midnight = datetime.combine(view.occurred_on, time(0), tzinfo=timezone)
    totals = dict.fromkeys(SleepStage, 0.0)
    segments: list[SleepSegment] = []
    for span in view.stages:
        totals[span.stage] += _minutes(span.started_at, span.ended_at)
        segments.append(
            SleepSegment(
                stage=span.stage,
                start_offset=_minutes(midnight, span.started_at),
                end_offset=_minutes(midnight, span.ended_at),
            )
        )
    in_bed = _minutes(view.started_at, view.ended_at)
    asleep = (
        totals[SleepStage.REM] + totals[SleepStage.LIGHT] + totals[SleepStage.DEEP]
        if view.stages
        else in_bed
    )
    return SleepNight(
        date=view.occurred_on,
        session_id=view.id,
        started_at=view.started_at,
        ended_at=view.ended_at,
        bed_offset=_minutes(midnight, view.started_at),
        wake_offset=_minutes(midnight, view.ended_at),
        in_bed_minutes=in_bed,
        asleep_minutes=asleep,
        stages=SleepStageMinutes(
            awake=totals[SleepStage.AWAKE],
            rem=totals[SleepStage.REM],
            light=totals[SleepStage.LIGHT],
            deep=totals[SleepStage.DEEP],
        ),
        segments=tuple(segments),
    )


def sleep_week_math(
    sessions: Sequence[SleepSessionView],
    as_of: date,
    timezone: tzinfo,
    days: int = SLEEP_WINDOW_DAYS,
) -> SleepWeekMath:
    """Nights in the `days` ending on `as_of`, one per local date (the longest session wins).

    `bed_spread` / `wake_spread` are the population standard deviation of bed and wake offsets
    in minutes, a consistency measure; they need at least two nights. `last_recorded_at` is the
    newest `created_at` over every session, not just the window, so it reports data freshness.
    """
    if days < 1:
        raise ValueError("days must be at least 1")
    range_start = as_of - timedelta(days=days - 1)
    main_by_day: dict[date, SleepSessionView] = {}
    for view in sessions:
        if not range_start <= view.occurred_on <= as_of:
            continue
        current = main_by_day.get(view.occurred_on)
        if current is None or _span(view) > _span(current):
            main_by_day[view.occurred_on] = view
    window: list[SleepDay] = []
    for offset in range(days):
        day = range_start + timedelta(days=offset)
        view = main_by_day.get(day)
        window.append(
            SleepDay(date=day, night=None if view is None else sleep_night(view, timezone))
        )
    nights = [day.night for day in window if day.night is not None]
    recorded = [_as_utc(view.created_at) for view in sessions if view.created_at is not None]
    staged = [night for night in nights if night.segments]
    return SleepWeekMath(
        as_of=as_of,
        range_start=range_start,
        range_end=as_of,
        night=window[-1].night,
        days=tuple(window),
        nights_logged=len(nights),
        average_asleep=_mean([night.asleep_minutes for night in nights]),
        average_bed_offset=_mean([night.bed_offset for night in nights]),
        average_wake_offset=_mean([night.wake_offset for night in nights]),
        average_stages=(
            None
            if not staged
            else SleepStageMinutes(
                awake=_mean([night.stages.awake for night in staged]) or 0.0,
                rem=_mean([night.stages.rem for night in staged]) or 0.0,
                light=_mean([night.stages.light for night in staged]) or 0.0,
                deep=_mean([night.stages.deep for night in staged]) or 0.0,
            )
        ),
        bed_spread=_spread([night.bed_offset for night in nights]),
        wake_spread=_spread([night.wake_offset for night in nights]),
        last_recorded_at=max(recorded, default=None),
    )


def _span(view: SleepSessionView) -> float:
    return _minutes(view.started_at, view.ended_at)


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _spread(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5


def _minutes(start: datetime, end: datetime) -> float:
    return (_as_utc(end) - _as_utc(start)).total_seconds() / 60.0


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
