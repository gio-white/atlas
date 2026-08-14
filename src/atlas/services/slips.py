from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session

from atlas.db.models import Entry
from atlas.domain import (
    Aggregation,
    Direction,
    Period,
    Source,
    ValueType,
    bucket_for,
    previous_bucket,
    rollup,
)
from atlas.services.clock import resolve_today
from atlas.services.entries import log_entry
from atlas.services.life import SLIP_METRIC_SLUG, ensure_life_metric
from atlas.services.lookups import entries_for_metric
from atlas.services.mapping import entry_view


@dataclass(frozen=True, slots=True)
class SlipsWeek:
    as_of: date
    week_start: date
    week_end: date
    this_week: float
    last_week: float
    delta_fraction: float | None
    series: list[float]


def ensure_slip_metric(session: Session):
    return ensure_life_metric(
        session,
        SLIP_METRIC_SLUG,
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.LOWER_IS_BETTER,
        name="Slip",
    )


def log_slip(
    session: Session,
    *,
    note: str | None = None,
    occurred_on: date | None = None,
    source: Source = Source.CLI,
) -> Entry:
    ensure_slip_metric(session)
    return log_entry(
        session,
        SLIP_METRIC_SLUG,
        1.0,
        occurred_on=occurred_on,
        note=note,
        source=source,
    )


def slips_week(session: Session, *, as_of: date | None = None) -> SlipsWeek:
    as_of = resolve_today(as_of)
    metric = ensure_slip_metric(session)
    views = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
    week = bucket_for(as_of, Period.WEEK)
    previous = previous_bucket(week)
    this_week = _sum_between(views, week.start, min(week.end, as_of))
    last_week = _sum_between(views, previous.start, previous.end)
    series: list[float] = []
    for offset in range(7):
        day = week.start + timedelta(days=offset)
        series.append(0.0 if day > as_of else _sum_between(views, day, day))
    delta = None if last_week == 0 else (this_week - last_week) / last_week
    return SlipsWeek(
        as_of=as_of,
        week_start=week.start,
        week_end=week.end,
        this_week=this_week,
        last_week=last_week,
        delta_fraction=delta,
        series=series,
    )


def _sum_between(views, start: date, end: date) -> float:
    return (
        rollup(
            [view for view in views if start <= view.occurred_on <= end],
            Aggregation.SUM,
        )
        or 0.0
    )
