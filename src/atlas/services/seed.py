from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import Any

from sqlmodel import Session, select

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.db.models import (
    Ambition,
    Goal,
    LibraryTitle,
    Metric,
    ScreenCategory,
    SideQuest,
    SleepSession,
    Task,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.port import import_all
from atlas.services.seed_quests import demo_quests
from atlas.settings import load_settings

HISTORY_DAYS = 28
WEEKDAYS = [1, 2, 3, 4, 5]
DOOMSCROLL_SLIPS = (23, 9)


@dataclass(frozen=True, slots=True)
class SeedSummary:
    as_of: date
    metrics: int
    habits: int
    entries: int
    screen_categories: int
    screen_apps: int
    screen_devices: int
    screen_sessions: int
    library_topics: int
    library_titles: int
    sleep_sessions: int
    ambitions: int = 0
    goals: int = 0
    milestones: int = 0
    side_quests: int = 0
    chapters: int = 0
    tasks: int = 0
    time_blocks: int = 0


def seed_demo(
    session: Session,
    *,
    as_of: date | None = None,
    replace: bool = False,
) -> SeedSummary:
    as_of = resolve_today(as_of)
    if not replace and _has_data(session):
        raise ValidationError("database already has data; pass --replace to overwrite")
    payload = demo_payload(as_of)
    import_all(session, payload, replace=replace)
    return SeedSummary(
        as_of=as_of,
        metrics=len(payload["metrics"]),
        habits=len(payload["habits"]),
        entries=len(payload["entries"]),
        screen_categories=len(payload["screen_categories"]),
        screen_apps=len(payload["screen_apps"]),
        screen_devices=len(payload["screen_devices"]),
        screen_sessions=len(payload["screen_sessions"]),
        library_topics=len(payload["library_topics"]),
        library_titles=len(payload["library_titles"]),
        sleep_sessions=len(payload["sleep_sessions"]),
        ambitions=len(payload["ambitions"]),
        goals=len(payload["goals"]),
        milestones=len(payload["milestones"]),
        side_quests=len(payload["side_quests"]),
        chapters=len(payload["chapters"]),
        tasks=len(payload["tasks"]),
        time_blocks=len(payload["time_blocks"]),
    )


def _has_data(session: Session) -> bool:
    """Whether anything a person (or a device) put in is already there. Every kind of data
    hangs off one of these tables, so an empty set of them means an empty database."""
    tables = (
        Metric,
        Task,
        Goal,
        Ambition,
        SideQuest,
        LibraryTitle,
        SleepSession,
        ScreenCategory,
    )
    return any(session.exec(select(table).limit(1)).first() is not None for table in tables)


def demo_payload(as_of: date, zone: tzinfo | None = None) -> dict[str, Any]:
    start = as_of - timedelta(days=HISTORY_DAYS - 1)
    zone = zone if zone is not None else load_settings().timezone
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "metrics": _metrics(),
        "habits": _habits(start, as_of),
        "habit_freezes": _habit_freezes(as_of),
        "screen_categories": _screen_categories(),
        "screen_apps": _screen_apps(),
        "screen_devices": _screen_devices(as_of, zone),
        "screen_budgets": _screen_budgets(start),
        "screen_sessions": _screen_sessions(start, as_of),
        "library_topics": _library_topics(),
        "library_titles": _library_titles(as_of),
        "sleep_sessions": _sleep_sessions(start, as_of),
        **demo_quests(as_of, zone),
        "entries": _entries(start, as_of),
    }


def _metrics() -> list[dict[str, Any]]:
    return [
        _metric("pushups", "manual", "count", "sum", unit="reps", direction="higher_is_better"),
        _metric(
            "weight",
            "manual",
            "quantity",
            "last",
            unit="kg",
            direction="lower_is_better",
        ),
        _metric("meditated", "manual", "bool", "sum", direction="higher_is_better"),
        _metric("coffee", "manual", "count", "sum", unit="cups", direction="lower_is_better"),
        _metric("runs", "manual", "count", "sum", direction="higher_is_better"),
        _metric(
            "no-doomscrolling",
            "habit",
            "count",
            "sum",
            unit="slips",
            direction="lower_is_better",
        ),
        _metric("mood", "manual", "rating", "mean", direction="higher_is_better"),
        _metric(
            "deep-work",
            "manual",
            "duration",
            "sum",
            unit="min",
            direction="higher_is_better",
        ),
        _metric("books", "manual", "count", "sum", direction="higher_is_better"),
        _metric("journal", "journal", "text", "last"),
        _metric(
            "savings",
            "manual",
            "quantity",
            "last",
            unit="EUR",
            direction="higher_is_better",
        ),
        _metric("called-family", "manual", "bool", "sum", direction="higher_is_better"),
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


def _habits(start: date, as_of: date) -> list[dict[str, Any]]:
    """One habit per kind of rule (habits brief §2): ticked every day, on some days, N times a
    week or a month, and read from sleep, screen time, and planned sessions. Ticked habits carry
    a Done mark on the days the demo person did them; data habits are judged from the data."""
    days = [day for day in _days(start, as_of) if not _demo_frozen(day, as_of)]
    first_weekday = next(day for day in days if day.isoweekday() <= 5)
    slips = {as_of - timedelta(days=offset) for offset in DOOMSCROLL_SLIPS}
    travel_day = as_of - timedelta(days=10)
    runs_changed = as_of - timedelta(days=11)
    return [
        _habit(
            "pushups-daily",
            "Morning pushups",
            start,
            [_manual_rule(start, "specific_days", weekdays=WEEKDAYS)],
            [d for d in days if d.isoweekday() <= 5 and d != first_weekday],
            time_of_day="morning",
        ),
        _habit(
            "meditated-daily",
            "Meditate",
            start,
            [_manual_rule(start, "every_day")],
            [d for d in days if (as_of - d).days % 7 != 3 and d != travel_day],
            time_of_day="morning",
        ),
        _habit(
            "deep-work-weekdays",
            "Deep work",
            start,
            [_manual_rule(start, "specific_days", weekdays=WEEKDAYS)],
            [d for d in days if d.isoweekday() <= 5 and d != first_weekday and d != as_of],
            time_of_day="morning",
        ),
        _habit(
            "wake-early",
            "Wake up early",
            start,
            [_data_rule(start, "every_day", "wake_time", "before", 7 * 60)],
            time_of_day="morning",
        ),
        _habit(
            "plan-the-day",
            "Plan the day",
            start,
            [_data_rule(start, "specific_days", "sessions_planned", "before", 12 * 60, WEEKDAYS)],
            time_of_day="morning",
        ),
        _habit(
            "coffee-daily",
            "One coffee at most",
            start,
            [_manual_rule(start, "every_day")],
            [d for d in days if d.isoweekday() != 5 and d != as_of],
            time_of_day="afternoon",
        ),
        _habit(
            "runs-weekly",
            "Run",
            start,
            [
                _manual_rule(start, "times_a_week", times=2),
                _manual_rule(runs_changed, "times_a_week", times=3),
            ],
            [d for d in days if d.isoweekday() in {1, 3, 6}],
        ),
        _habit(
            "family-monthly",
            "Call family",
            start,
            [_manual_rule(start, "times_a_month", times=2)],
            [d for d in days if d.isoweekday() == 7],
            time_of_day="evening",
        ),
        _habit(
            "no-doomscrolling",
            "No doomscrolling",
            start,
            [_manual_rule(start, "every_day")],
            [d for d in days if d not in slips and d != as_of],
            time_of_day="evening",
        ),
        _habit(
            "bad-apps-cap",
            "Keep Bad apps short",
            start,
            [_data_rule(start, "every_day", "screen_bad_apps", "at_most", 90)],
            time_of_day="evening",
        ),
        _habit(
            "instagram-cap",
            "Instagram under half an hour",
            start,
            [_data_rule(start, "every_day", "screen_app", "at_most", 30, ref="instagram")],
            time_of_day="evening",
        ),
        _habit(
            "read-before-bed",
            "Read before bed",
            start,
            [_manual_rule(start, "every_day")],
            [d for d in days if d < as_of - timedelta(days=6) and d.toordinal() % 3 != 0],
            time_of_day="evening",
            archived_on=as_of - timedelta(days=5),
        ),
    ]


def _habit_freezes(as_of: date) -> list[dict[str, Any]]:
    holiday_start, holiday_end = _demo_holiday(as_of)
    travel_day = as_of - timedelta(days=10)
    return [
        {
            "habit": None,
            "start_on": holiday_start.isoformat(),
            "end_on": holiday_end.isoformat(),
            "reason": "Holiday",
        },
        {
            "habit": "meditated-daily",
            "start_on": travel_day.isoformat(),
            "end_on": travel_day.isoformat(),
            "reason": "Travel day",
        },
    ]


def _demo_holiday(as_of: date) -> tuple[date, date]:
    return as_of - timedelta(days=18), as_of - timedelta(days=16)


def _demo_frozen(day: date, as_of: date) -> bool:
    start, end = _demo_holiday(as_of)
    return start <= day <= end


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
    for offset, note in zip(DOOMSCROLL_SLIPS, ("Late night feed", "Couldn't sleep"), strict=True):
        entries.append(_num("no-doomscrolling", as_of - timedelta(days=offset), 1.0, note=note))
    entries.append(_text("journal", as_of - timedelta(days=7), "Week started slow."))
    entries.append(_text("journal", as_of - timedelta(days=1), "Wrapped the deep-work block."))
    return entries


def _library_topics() -> list[dict[str, Any]]:
    return [
        {"slug": "programming", "name": "Programming", "archived_at": None},
        {"slug": "physics", "name": "Physics", "archived_at": None},
        {"slug": "finance", "name": "Finance", "archived_at": None},
        {"slug": "math", "name": "Math", "archived_at": None},
    ]


def _library_titles(as_of: date) -> list[dict[str, Any]]:
    return [
        _library_title(
            "atomic-habits",
            "Atomic Habits",
            "book",
            creator="James Clear",
            status="done",
            topics=["finance"],
            finished_on=as_of - timedelta(days=10),
            started_on=as_of - timedelta(days=24),
            rating=4,
        ),
        _library_title(
            "the-office",
            "The Office",
            "series",
            creator="Greg Daniels",
            status="in_progress",
            progress="S3E4",
            started_on=as_of - timedelta(days=20),
        ),
        _library_title(
            "interstellar",
            "Interstellar",
            "film",
            creator="Christopher Nolan",
            recommended_by="Alex",
            status="done",
            topics=["physics"],
            finished_on=as_of - timedelta(days=3),
            started_on=as_of - timedelta(days=3),
            rating=5,
        ),
        _library_title(
            "lex-fridman-109",
            "Lex Fridman #109",
            "podcast",
            creator="Lex Fridman",
            status="done",
            topics=["programming"],
            finished_on=as_of - timedelta(days=1),
            rating=3,
            link="https://lexfridman.com/podcast/",
        ),
        _library_title(
            "three-body",
            "The Three-Body Problem",
            "book",
            creator="Liu Cixin",
            recommended_by="Sam",
            status="queued",
            topics=["physics"],
        ),
        _library_title(
            "neon-genesis",
            "Neon Genesis Evangelion",
            "anime",
            creator="Hideaki Anno",
            status="dropped",
            started_on=as_of - timedelta(days=15),
            progress="S1E6",
            rating=2,
        ),
        _library_title(
            "kind-of-blue",
            "Kind of Blue",
            "music",
            creator="Miles Davis",
            recommended_by="Alex",
            status="done",
            finished_on=as_of - timedelta(days=2),
            rating=5,
        ),
        _library_title(
            "3blue1brown-linear",
            "Essence of Linear Algebra",
            "video",
            creator="3Blue1Brown",
            status="done",
            topics=["math"],
            finished_on=as_of - timedelta(days=5),
            rating=5,
            link="https://www.3blue1brown.com/topics/linear-algebra",
        ),
        _library_title(
            "rich-dad",
            "Rich Dad Poor Dad",
            "book",
            creator="Robert Kiyosaki",
            status="queued",
            topics=["finance"],
        ),
    ]


def _library_title(
    slug: str,
    name: str,
    kind: str,
    *,
    creator: str | None = None,
    recommended_by: str | None = None,
    status: str = "queued",
    topics: list[str] | None = None,
    started_on: date | None = None,
    finished_on: date | None = None,
    progress: str | None = None,
    note: str | None = None,
    rating: int | None = None,
    link: str | None = None,
) -> dict[str, Any]:
    created = finished_on or started_on or date(2026, 8, 1)
    created_at = datetime(created.year, created.month, created.day, 12, 0, tzinfo=UTC)
    return {
        "slug": slug,
        "name": name,
        "kind": kind,
        "creator": creator,
        "recommended_by": recommended_by,
        "status": status,
        "started_on": started_on.isoformat() if started_on else None,
        "finished_on": finished_on.isoformat() if finished_on else None,
        "progress": progress,
        "note": note,
        "rating": rating,
        "link": link,
        "topics": topics or [],
        "image_url": None,
        "image_media_type": None,
        "image_base64": None,
        "archived_at": None,
        "created_at": created_at.isoformat(),
    }


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


def _screen_devices(as_of: date, zone: tzinfo) -> list[dict[str, Any]]:
    """The phone has sent everything up to midnight; the laptop up to noon today, so a screen
    habit is already judged for yesterday and still waiting for today (habits brief §3)."""

    def through(hour: int) -> str:
        local = datetime.combine(as_of, time(hour, 0), zone)
        return local.astimezone(UTC).isoformat()

    return [
        {"slug": "iphone", "name": "iPhone", "archived_at": None, "complete_through": through(0)},
        {
            "slug": "macbook",
            "name": "MacBook",
            "archived_at": None,
            "complete_through": through(12),
        },
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


SLEEP_BEDTIMES = [(23, 10), (23, 40), (22, 55), (0, 20), (23, 25), (0, 5), (23, 50)]
SLEEP_CYCLE_DEEP = [45, 35, 20, 10, 0, 0]
SLEEP_CYCLE_REM = [10, 18, 24, 30, 32, 32]


def _sleep_sessions(start: date, as_of: date) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for index, wake_day in enumerate(_days(start + timedelta(days=1), as_of)):
        if index % 9 == 4:
            continue
        hour, minute = SLEEP_BEDTIMES[index % len(SLEEP_BEDTIMES)]
        bed_day = wake_day if hour < 12 else wake_day - timedelta(days=1)
        started = datetime(bed_day.year, bed_day.month, bed_day.day, hour, minute, tzinfo=UTC)
        weekend = wake_day.isoweekday() >= 6
        wake_minutes = (8 * 60 + 15 if weekend else 6 * 60 + 50) + (index * 7) % 25
        ended = datetime(wake_day.year, wake_day.month, wake_day.day, tzinfo=UTC) + timedelta(
            minutes=wake_minutes
        )
        sessions.append(_sleep_session(started, ended, index))
    return sessions


def _sleep_session(started: datetime, ended: datetime, index: int) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    cursor = started

    def add(stage: str, minutes: float) -> None:
        nonlocal cursor
        if minutes <= 0 or cursor >= ended:
            return
        stop = min(cursor + timedelta(minutes=minutes), ended)
        stages.append(
            {"stage": stage, "started_at": cursor.isoformat(), "ended_at": stop.isoformat()}
        )
        cursor = stop

    add("awake", 8 + index % 4 * 3)
    cycle = 0
    while cursor < ended:
        add("light", 28 + (index + cycle) % 3 * 6)
        add("deep", SLEEP_CYCLE_DEEP[min(cycle, len(SLEEP_CYCLE_DEEP) - 1)])
        add("light", 14)
        add("rem", SLEEP_CYCLE_REM[min(cycle, len(SLEEP_CYCLE_REM) - 1)])
        if (index + cycle) % 4 == 1:
            add("awake", 4)
        cycle += 1
    return {
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "occurred_on": ended.date().isoformat(),
        "note": None,
        "source": "import",
        "created_at": ended.isoformat(),
        "stages": stages,
    }


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


def _metric(
    slug: str,
    origin: str,
    value_type: str,
    aggregation: str,
    *,
    unit: str | None = None,
    direction: str = "neutral",
    name: str | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "origin": origin,
        "name": name if name is not None else slug.replace("-", " ").title(),
        "value_type": value_type,
        "unit": unit,
        "aggregation": aggregation,
        "direction": direction,
        "archived_at": None,
    }


def _habit(
    slug: str,
    name: str,
    first_day: date,
    rules: list[dict[str, Any]],
    done_days: list[date] | None = None,
    *,
    time_of_day: str = "anytime",
    archived_on: date | None = None,
) -> dict[str, Any]:
    archived_at = (
        datetime(archived_on.year, archived_on.month, archived_on.day, 20, 0, tzinfo=UTC)
        if archived_on
        else None
    )
    return {
        "slug": slug,
        "name": name,
        "time_of_day": time_of_day,
        "first_day": first_day.isoformat(),
        "archived_at": archived_at.isoformat() if archived_at else None,
        "rules": rules,
        "marks": [{"day": day.isoformat(), "result": "done"} for day in done_days or []],
    }


def _manual_rule(
    starts_on: date,
    frequency: str,
    *,
    weekdays: list[int] | None = None,
    times: int | None = None,
) -> dict[str, Any]:
    return {
        "starts_on": starts_on.isoformat(),
        "frequency": frequency,
        "weekdays": weekdays,
        "times": times,
        "check": "manual",
        "source": None,
        "source_ref": None,
        "threshold": None,
        "value": None,
    }


def _data_rule(
    starts_on: date,
    frequency: str,
    source: str,
    threshold: str,
    value: float,
    weekdays: list[int] | None = None,
    *,
    ref: str | None = None,
) -> dict[str, Any]:
    return {
        **_manual_rule(starts_on, frequency, weekdays=weekdays),
        "check": "data",
        "source": source,
        "source_ref": ref,
        "threshold": threshold,
        "value": float(value),
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
