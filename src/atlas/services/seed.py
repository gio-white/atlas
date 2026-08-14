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
        "screen_categories": _screen_categories(),
        "screen_apps": _screen_apps(),
        "screen_devices": _screen_devices(),
        "screen_budgets": _screen_budgets(start),
        "screen_sessions": _screen_sessions(start, as_of),
        "entries": _entries(start, as_of),
    }


def _areas() -> list[dict[str, Any]]:
    return [
        _area("health", "Health", "Body, energy, and daily practice."),
        _area("career", "Career", "Deep work and making things."),
        _area("finance", "Finance", "Runway and buffers."),
        _area("relationships", "Relationships", "People who matter."),
        _area("screen", "Screen", "Apps, categories, and budgets."),
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
        _metric(
            "instagram",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="lower_is_better",
            name="Instagram",
        ),
        _metric(
            "youtube",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="lower_is_better",
            name="YouTube",
        ),
        _metric(
            "whatsapp",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="neutral",
            name="WhatsApp",
        ),
        _metric(
            "vscode",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="higher_is_better",
            name="VS Code",
        ),
        _metric(
            "chatgpt",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="higher_is_better",
            name="ChatGPT",
        ),
        _metric(
            "netflix",
            "screen",
            "duration",
            "sum",
            unit="min",
            direction="lower_is_better",
            name="Netflix",
        ),
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
            None,
            "Durable health",
            "milestone",
            long_start,
            long_due,
            horizon="long",
            description="Stay strong, light, and consistent for years.",
        ),
        _goal(
            "financial-freedom",
            None,
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


def _screen_categories() -> list[dict[str, Any]]:
    return [
        _screen_category("entertainment", "Entertainment", "waste"),
        _screen_category("social", "Social", "waste"),
        _screen_category("productivity", "Productivity", "useful"),
        _screen_category("learning", "Learning", "useful"),
    ]


def _screen_apps() -> list[dict[str, Any]]:
    return [
        _screen_app("instagram", "Instagram", "social"),
        _screen_app("youtube", "YouTube", "entertainment"),
        _screen_app("whatsapp", "WhatsApp", "social"),
        _screen_app("vscode", "VS Code", "productivity"),
        _screen_app("chatgpt", "ChatGPT", "learning"),
        _screen_app("netflix", "Netflix", "entertainment"),
    ]


def _screen_devices() -> list[dict[str, Any]]:
    return [
        {"slug": "iphone", "name": "iPhone", "archived_at": None},
        {"slug": "macbook", "name": "MacBook", "archived_at": None},
    ]


def _screen_budgets(start: date) -> list[dict[str, Any]]:
    return [
        {
            "slug": "waste-cap",
            "name": "Waste cap",
            "target_kind": "judgment",
            "target_slug": "waste",
            "period": "day",
            "target_value": 90.0,
            "comparator": "at_most",
            "active_from": start.isoformat(),
            "active_to": None,
        }
    ]


def _screen_sessions(start: date, as_of: date) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    days = list(_days(start, as_of))
    for index, day in enumerate(days):
        weekday = day.isoweekday()
        if weekday <= 5:
            sessions.append(_interval("vscode", day, 9, 0, 10, 30, device="macbook"))
            if weekday in {2, 4}:
                sessions.append(_interval("chatgpt", day, 12, 0, 12, 25, device="macbook"))
            sessions.append(_interval("youtube", day, 20, 0, 20, 35, device="iphone"))
            sessions.append(_interval("instagram", day, 20, 40, 21, 0, device="iphone"))
            if weekday == 5:
                sessions.append(_interval("netflix", day, 21, 30, 22, 45, device="iphone"))
        else:
            sessions.append(_interval("youtube", day, 14, 0, 16, 0, device="iphone"))
            sessions.append(_interval("instagram", day, 16, 5, 16, 40, device="iphone"))
            sessions.append(_interval("youtube", day, 21, 0, 22, 20, device="iphone"))
            sessions.append(_interval("instagram", day, 22, 25, 22, 50, device="iphone"))
        if weekday == 6 and index % 2 == 0:
            sessions.append(
                _interval("youtube", day, 23, 30, 0, 45, device="iphone", next_day=True)
            )
        if index in {3, 11, 19, 26}:
            sessions.append(_duration("whatsapp", day, 12.0 + index % 5, device="iphone"))
        if index == 8:
            sessions.append(_duration("instagram", day, 18.0))
    return sessions


def _screen_category(slug: str, name: str, judgment: str) -> dict[str, Any]:
    return {"slug": slug, "name": name, "judgment": judgment, "archived_at": None}


def _screen_app(slug: str, name: str, category: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "name": name,
        "category": category,
        "metric": slug,
        "archived_at": None,
    }


def _interval(
    app: str,
    day: date,
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int,
    *,
    device: str | None = None,
    next_day: bool = False,
) -> dict[str, Any]:
    started = datetime(day.year, day.month, day.day, start_hour, start_minute, tzinfo=UTC)
    end_day = day + timedelta(days=1) if next_day else day
    ended = datetime(end_day.year, end_day.month, end_day.day, end_hour, end_minute, tzinfo=UTC)
    minutes = (ended - started).total_seconds() / 60.0
    return {
        "app": app,
        "device": device,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "minutes": minutes,
        "occurred_on": day.isoformat(),
        "note": None,
        "source": "import",
        "created_at": ended.isoformat(),
    }


def _duration(
    app: str,
    day: date,
    minutes: float,
    *,
    device: str | None = None,
) -> dict[str, Any]:
    created = datetime(day.year, day.month, day.day, 12, 0, tzinfo=UTC)
    return {
        "app": app,
        "device": device,
        "started_at": None,
        "ended_at": None,
        "minutes": minutes,
        "occurred_on": day.isoformat(),
        "note": None,
        "source": "import",
        "created_at": created.isoformat(),
    }


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
    name: str | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "area": area,
        "name": name if name is not None else slug.replace("-", " ").title(),
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
    area: str | None,
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
