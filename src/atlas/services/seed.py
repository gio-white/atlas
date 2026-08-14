from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlmodel import Session

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.services.areas import list_areas
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.port import import_all

HISTORY_DAYS = 28
WEEKDAYS = [1, 2, 3, 4, 5]


@dataclass(frozen=True, slots=True)
class SeedSummary:
    as_of: date
    areas: int
    metrics: int
    habits: int
    goals: int
    milestones: int
    entries: int


def seed_demo(
    session: Session,
    *,
    as_of: date | None = None,
    replace: bool = False,
) -> SeedSummary:
    as_of = resolve_today(as_of)
    if not replace and list_areas(session, include_archived=True):
        raise ValidationError("database already has data; pass --replace to overwrite")
    payload = demo_payload(as_of)
    import_all(session, payload, replace=replace)
    return SeedSummary(
        as_of=as_of,
        areas=len(payload["areas"]),
        metrics=len(payload["metrics"]),
        habits=len(payload["habits"]),
        goals=len(payload["goals"]),
        milestones=len(payload["milestones"]),
        entries=len(payload["entries"]),
    )


def demo_payload(as_of: date) -> dict[str, Any]:
    start = as_of - timedelta(days=HISTORY_DAYS - 1)
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "areas": _areas(),
        "metrics": _metrics(),
        "habits": _habits(start),
        "goals": _goals(as_of),
        "milestones": _milestones(as_of),
        "tasks": _tasks(as_of),
        "entries": _entries(start, as_of),
    }


def _areas() -> list[dict[str, Any]]:
    return [
        _area("health", "Health", "Body, energy, and daily practice."),
        _area("career", "Career", "Deep work and making things."),
        _area("finance", "Finance", "Runway and buffers."),
        _area("relationships", "Relationships", "People who matter."),
    ]


def _metrics() -> list[dict[str, Any]]:
    return [
        _metric("pushups", "health", "count", "sum", unit="reps", direction="higher_is_better"),
        _metric(
            "weight",
            "health",
            "quantity",
            "last",
            unit="kg",
            direction="lower_is_better",
        ),
        _metric("meditated", "health", "bool", "sum", direction="higher_is_better"),
        _metric("coffee", "health", "count", "sum", unit="cups", direction="lower_is_better"),
        _metric("runs", "health", "count", "sum", direction="higher_is_better"),
        _metric("mood", "health", "rating", "mean", direction="higher_is_better"),
        _metric(
            "deep-work",
            "career",
            "duration",
            "sum",
            unit="min",
            direction="higher_is_better",
        ),
        _metric("books", "career", "count", "sum", direction="higher_is_better"),
        _metric("journal", "career", "text", "last"),
        _metric(
            "savings",
            "finance",
            "quantity",
            "last",
            unit="EUR",
            direction="higher_is_better",
        ),
        _metric("called-family", "relationships", "bool", "sum", direction="higher_is_better"),
    ]


def _habits(start: date) -> list[dict[str, Any]]:
    return [
        _habit("pushups-daily", "pushups", "day", 40.0, "at_least", start, weekdays=WEEKDAYS),
        _habit("meditated-daily", "meditated", "day", 1.0, "at_least", start),
        _habit("coffee-daily", "coffee", "day", 1.0, "at_most", start),
        _habit("runs-weekly", "runs", "week", 3.0, "at_least", start),
        _habit(
            "deep-work-weekdays",
            "deep-work",
            "day",
            90.0,
            "at_least",
            start,
            weekdays=WEEKDAYS,
        ),
        _habit("family-monthly", "called-family", "month", 2.0, "at_least", start),
    ]


def _goals(as_of: date) -> list[dict[str, Any]]:
    long_start = as_of - timedelta(days=200)
    long_due = as_of + timedelta(days=530)
    return [
        _goal(
            "durable-health",
            "health",
            "Durable health",
            "milestone",
            long_start,
            long_due,
            horizon="long",
            description="Stay strong, light, and consistent for years.",
        ),
        _goal(
            "financial-freedom",
            "finance",
            "Financial freedom",
            "milestone",
            long_start,
            long_due,
            horizon="long",
            description="Runway and buffers so work is a choice.",
        ),
        _goal(
            "bodyweight-75",
            "health",
            "Bodyweight 75kg",
            "metric_target",
            as_of - timedelta(days=90),
            as_of + timedelta(days=90),
            metric="weight",
            target_value=75.0,
            comparator="at_most",
            baseline_value=82.0,
            measure="latest_value",
            horizon="medium",
            parent="durable-health",
            description="Land at a sustainable racing weight.",
        ),
        _goal(
            "read-12-books",
            "career",
            "Read 12 books",
            "metric_target",
            as_of - timedelta(days=200),
            as_of + timedelta(days=165),
            metric="books",
            target_value=12.0,
            comparator="at_least",
            measure="cumulative_since_start",
            horizon="long",
            description="A book a month, with room to miss one.",
        ),
        _goal(
            "emergency-fund",
            "finance",
            "Emergency fund €5k",
            "metric_target",
            as_of - timedelta(days=180),
            as_of + timedelta(days=180),
            metric="savings",
            target_value=5000.0,
            comparator="at_least",
            measure="latest_value",
            horizon="medium",
            parent="financial-freedom",
            description="Three months of expenses in cash.",
        ),
        _goal(
            "ship-side-project",
            "career",
            "Ship the side project",
            "milestone",
            as_of - timedelta(days=45),
            as_of + timedelta(days=90),
            horizon="medium",
            description="Spec, MVP, first user.",
        ),
        _goal(
            "workout-this-week",
            "health",
            "Workout four times",
            "milestone",
            as_of - timedelta(days=1),
            as_of + timedelta(days=6),
            horizon="short",
            parent="bodyweight-75",
            description="Four sessions this week to keep the streak honest.",
        ),
    ]


def _milestones(as_of: date) -> list[dict[str, Any]]:
    hit_78 = as_of - timedelta(days=14)
    spec = as_of - timedelta(days=30)
    return [
        _milestone("bodyweight-75", "Hit 78kg", hit_78, done_on=hit_78),
        _milestone("bodyweight-75", "Hit 76kg", as_of + timedelta(days=30)),
        _milestone("ship-side-project", "Spec written", spec, done_on=spec),
        _milestone("ship-side-project", "MVP shipped", as_of + timedelta(days=21)),
        _milestone("ship-side-project", "First user", as_of + timedelta(days=75)),
        _milestone("durable-health", "Keep a 30-day streak", as_of + timedelta(days=30)),
        _milestone("workout-this-week", "Four sessions", as_of + timedelta(days=6)),
    ]


def _entries(start: date, as_of: date) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    first_weekday = next(day for day in _days(start, as_of) if day.isoweekday() <= 5)

    for day in _days(start, as_of):
        iso = day.isoweekday()
        if iso <= 5 and day != first_weekday:
            entries.append(_num("pushups", day, 40.0 if iso < 5 else 50.0))
            entries.append(_num("deep-work", day, 90.0 + 15.0 * (iso - 1)))
        if (as_of - day).days % 7 != 3:
            entries.append(_bool("meditated", day, True))
        if iso <= 4:
            entries.append(_num("coffee", day, 1.0))
        elif iso == 5:
            entries.append(_num("coffee", day, 2.0))
        if iso in {1, 3, 6}:
            entries.append(_num("runs", day, 1.0))
        if iso == 7:
            entries.append(_bool("called-family", day, True))
        if iso in {1, 4}:
            entries.append(_num("mood", day, float(3 + day.toordinal() % 3)))

    for weeks in range(6):
        day = as_of - timedelta(days=14 * weeks)
        entries.append(_num("weight", day, round(77.4 + 0.6 * weeks, 1)))
    for i, offset in enumerate((180, 140, 100, 55, 12)):
        entries.append(_num("books", as_of - timedelta(days=offset), 1.0, note=f"book {i + 1}"))
    for offset, value in ((150, 1000.0), (90, 1800.0), (40, 2600.0), (0, 3200.0)):
        entries.append(_num("savings", as_of - timedelta(days=offset), value))
    entries.append(_text("journal", as_of - timedelta(days=7), "Week started slow."))
    entries.append(_text("journal", as_of - timedelta(days=1), "Wrapped the deep-work block."))
    return entries


def _tasks(as_of: date) -> list[dict[str, Any]]:
    noon = datetime(as_of.year, as_of.month, as_of.day, 12, 0, tzinfo=UTC)
    morning = datetime(as_of.year, as_of.month, as_of.day, 7, 0, tzinfo=UTC)
    done_at = datetime(as_of.year, as_of.month, as_of.day, 8, 0, tzinfo=UTC)
    return [
        {
            "title": "Pushups - 3 sets",
            "bucket": "today",
            "due_on": as_of.isoformat(),
            "due_at": None,
            "priority": "normal",
            "goal": "workout-this-week",
            "done_at": done_at.isoformat(),
            "created_at": noon.isoformat(),
        },
        {
            "title": "Meditate for 10 minutes",
            "bucket": "today",
            "due_on": as_of.isoformat(),
            "due_at": morning.isoformat(),
            "priority": "normal",
            "goal": "workout-this-week",
            "done_at": None,
            "created_at": noon.isoformat(),
        },
        {
            "title": "Evening walk",
            "bucket": "today",
            "due_on": None,
            "due_at": None,
            "priority": "low",
            "goal": "workout-this-week",
            "done_at": None,
            "created_at": noon.isoformat(),
        },
    ]


def _area(slug: str, name: str, description: str) -> dict[str, Any]:
    return {"slug": slug, "name": name, "description": description, "archived_at": None}


def _metric(
    slug: str,
    area: str,
    value_type: str,
    aggregation: str,
    *,
    unit: str | None = None,
    direction: str = "neutral",
) -> dict[str, Any]:
    return {
        "slug": slug,
        "area": area,
        "name": slug.replace("-", " ").title(),
        "value_type": value_type,
        "unit": unit,
        "aggregation": aggregation,
        "direction": direction,
        "archived_at": None,
    }


def _habit(
    slug: str,
    metric: str,
    period: str,
    target_value: float,
    comparator: str,
    active_from: date,
    *,
    weekdays: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "metric": metric,
        "name": slug.replace("-", " ").title(),
        "period": period,
        "target_value": target_value,
        "comparator": comparator,
        "weekdays": weekdays,
        "active_from": active_from.isoformat(),
        "active_to": None,
    }


def _goal(
    slug: str,
    area: str,
    name: str,
    kind: str,
    start_on: date,
    due_on: date,
    *,
    metric: str | None = None,
    target_value: float | None = None,
    comparator: str | None = None,
    baseline_value: float | None = None,
    measure: str | None = None,
    horizon: str | None = None,
    parent: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "area": area,
        "name": name,
        "kind": kind,
        "metric": metric,
        "target_value": target_value,
        "comparator": comparator,
        "baseline_value": baseline_value,
        "measure": measure,
        "start_on": start_on.isoformat(),
        "due_on": due_on.isoformat(),
        "horizon": horizon,
        "parent": parent,
        "description": description,
        "status": "active",
        "achieved_at": None,
    }


def _milestone(
    goal: str,
    name: str,
    due_on: date,
    *,
    done_on: date | None = None,
) -> dict[str, Any]:
    done_at = None
    if done_on is not None:
        done_at = datetime(done_on.year, done_on.month, done_on.day, 12, 0, tzinfo=UTC).isoformat()
    return {
        "goal": goal,
        "name": name,
        "due_on": due_on.isoformat(),
        "done_at": done_at,
    }


def _num(metric: str, day: date, value: float, note: str | None = None) -> dict[str, Any]:
    return _entry(metric, day, value_num=value, note=note)


def _bool(metric: str, day: date, value: bool) -> dict[str, Any]:
    return _entry(metric, day, value_bool=value)


def _text(metric: str, day: date, value: str) -> dict[str, Any]:
    return _entry(metric, day, value_text=value)


def _entry(
    metric: str,
    day: date,
    *,
    value_num: float | None = None,
    value_bool: bool | None = None,
    value_text: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    created = datetime(day.year, day.month, day.day, 12, 0, tzinfo=UTC)
    return {
        "metric": metric,
        "occurred_on": day.isoformat(),
        "occurred_at": None,
        "value_num": value_num,
        "value_bool": value_bool,
        "value_text": value_text,
        "note": note,
        "source": "import",
        "created_at": created.isoformat(),
    }


def _days(start: date, end: date) -> Iterator[date]:
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)
