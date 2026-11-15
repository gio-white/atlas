import base64
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any

from sqlmodel import Session, select

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.db.models import (
    Entry,
    Habit,
    HabitFreeze,
    HabitMark,
    HabitRule,
    HabitSupport,
    LibraryTitle,
    LibraryTitleTopic,
    LibraryTopic,
    Metric,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    ScreenDevice,
    ScreenSession,
    SleepSession,
    SleepSessionStage,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    EntryView,
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
    ScreenJudgment,
    SleepStage,
    Source,
    TimeOfDay,
    ValueType,
)
from atlas.domain.habit_migration import LegacyHabit, convert_legacy_habit
from atlas.domain.quests import QuestKind
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    require_habit,
    require_library_topic,
    require_metric,
    require_screen_app,
    require_screen_category,
    require_screen_device,
)
from atlas.services.quest_port import (
    LEGACY_SECTIONS,
    QUEST_SECTIONS,
    clear_quests,
    export_quests,
    import_quests,
)
from atlas.services.quests import SUPPORT_COLUMNS
from atlas.services.slugs import normalize_slug

QUESTS_SCHEMA_VERSION = 11
ORIGIN_SCHEMA_VERSION = 12
LIBRARY_SCHEMA_VERSION = 13
SUPPORTS_SCHEMA_VERSION = 14
HABIT_RULES_SCHEMA_VERSION = 15
AREAS_SECTION = "areas"

# What an export older than schema 12 says about a metric through its area.
_ORIGIN_BY_LEGACY_AREA = {"habits": MetricOrigin.HABIT, "screen": MetricOrigin.SCREEN}
_JOURNAL_METRIC_SLUG = "journal"


@dataclass(frozen=True, slots=True)
class ImportSummary:
    schema_version: int
    ignored_sections: tuple[str, ...] = ()

    @property
    def notes(self) -> list[str]:
        notes: list[str] = []
        legacy = [name for name in self.ignored_sections if name != AREAS_SECTION]
        if legacy:
            notes.append(
                f"Skipped {', '.join(legacy)} from this version {self.schema_version} export: "
                "quests replaced the old goals and tasks."
            )
        if AREAS_SECTION in self.ignored_sections:
            notes.append(
                f"Skipped areas from this version {self.schema_version} export: Atlas no longer "
                "groups metrics into areas. Every metric and habit was kept."
            )
        return notes


def export_all(session: Session) -> dict[str, Any]:
    metrics = list(session.exec(select(Metric).order_by(Metric.slug)).all())
    habits = list(session.exec(select(Habit).order_by(Habit.slug)).all())
    rules_by_habit: dict[int | None, list[HabitRule]] = {}
    for rule in session.exec(select(HabitRule).order_by(HabitRule.starts_on)).all():
        rules_by_habit.setdefault(rule.habit_id, []).append(rule)
    marks_by_habit: dict[int | None, list[HabitMark]] = {}
    for mark in session.exec(select(HabitMark).order_by(HabitMark.day)).all():
        marks_by_habit.setdefault(mark.habit_id, []).append(mark)
    freezes = list(session.exec(select(HabitFreeze).order_by(HabitFreeze.start_on)).all())
    habit_by_id = {habit.id: habit.slug for habit in habits}
    screen_categories = list(
        session.exec(select(ScreenCategory).order_by(ScreenCategory.slug)).all()
    )
    screen_apps = list(session.exec(select(ScreenApp).order_by(ScreenApp.slug)).all())
    screen_budgets = list(session.exec(select(ScreenBudget).order_by(ScreenBudget.slug)).all())
    screen_devices = list(session.exec(select(ScreenDevice).order_by(ScreenDevice.slug)).all())
    screen_sessions = list(session.exec(select(ScreenSession).order_by(ScreenSession.id)).all())
    library_topics = list(session.exec(select(LibraryTopic).order_by(LibraryTopic.slug)).all())
    library_titles = list(session.exec(select(LibraryTitle).order_by(LibraryTitle.slug)).all())
    library_links = list(session.exec(select(LibraryTitleTopic)).all())
    sleep_sessions = list(session.exec(select(SleepSession).order_by(SleepSession.id)).all())
    sleep_stage_rows = list(
        session.exec(select(SleepSessionStage).order_by(SleepSessionStage.started_at)).all()
    )
    entries = list(session.exec(select(Entry).order_by(Entry.occurred_on, Entry.id)).all())

    metric_by_id = {metric.id: metric.slug for metric in metrics}
    category_by_id = {category.id: category.slug for category in screen_categories}
    device_by_id = {device.id: device.slug for device in screen_devices}
    app_by_id = {app.id: app.slug for app in screen_apps}
    topic_by_id = {topic.id: topic.slug for topic in library_topics}
    topics_by_title: dict[int | None, list[str]] = {}
    for link in library_links:
        slug = topic_by_id.get(link.topic_id)
        if slug is None:
            continue
        topics_by_title.setdefault(link.title_id, []).append(slug)
    for slugs in topics_by_title.values():
        slugs.sort()
    stages_by_sleep: dict[int | None, list[SleepSessionStage]] = {}
    for stage in sleep_stage_rows:
        stages_by_sleep.setdefault(stage.session_id, []).append(stage)

    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "metrics": [_export_metric(metric) for metric in metrics],
        "habits": [
            _export_habit(habit, rules_by_habit.get(habit.id, []), marks_by_habit.get(habit.id, []))
            for habit in habits
        ],
        "habit_freezes": [_export_habit_freeze(row, habit_by_id) for row in freezes],
        "screen_categories": [_export_screen_category(row) for row in screen_categories],
        "screen_apps": [
            _export_screen_app(row, category_by_id, metric_by_id) for row in screen_apps
        ],
        "screen_budgets": [_export_screen_budget(row) for row in screen_budgets],
        "screen_devices": [_export_screen_device(row) for row in screen_devices],
        "screen_sessions": [
            _export_screen_session(row, app_by_id, device_by_id) for row in screen_sessions
        ],
        "library_topics": [_export_library_topic(row) for row in library_topics],
        "library_titles": [
            _export_library_title(row, topics_by_title.get(row.id, [])) for row in library_titles
        ],
        "sleep_sessions": [
            _export_sleep_session(row, stages_by_sleep.get(row.id, [])) for row in sleep_sessions
        ],
        **export_quests(session),
        "habit_supports": _export_habit_supports(session),
        "entries": [_export_entry(entry, metric_by_id) for entry in entries],
    }


def import_all(
    session: Session, payload: dict[str, Any], *, replace: bool = False
) -> ImportSummary:
    version = payload.get("schema_version")
    if version not in set(range(1, CURRENT_SCHEMA_VERSION + 1)):
        raise ValidationError(
            f"unsupported export schema_version {version!r}; "
            f"expected 1 through {CURRENT_SCHEMA_VERSION}"
        )
    has_quests = version >= QUESTS_SCHEMA_VERSION
    ignored = () if has_quests else tuple(key for key in LEGACY_SECTIONS if payload.get(key))
    legacy_areas = payload.get(AREAS_SECTION, []) if version < ORIGIN_SCHEMA_VERSION else []
    if legacy_areas:
        ignored = (*ignored, AREAS_SECTION)
    archived_areas = {
        normalize_slug(_require(raw, "slug")): _parse_datetime(raw.get("archived_at"))
        for raw in legacy_areas
        if raw.get("archived_at")
    }
    try:
        if replace:
            _clear_user_data(session)
        for raw in payload.get("metrics", []):
            _import_metric(session, raw, archived_areas)
        session.flush()
        for raw in payload.get("screen_categories", []):
            _import_screen_category(session, raw)
        session.flush()
        for raw in payload.get("screen_apps", []):
            _import_screen_app(session, raw)
        session.flush()
        for raw in payload.get("screen_budgets", []):
            _import_screen_budget(session, raw)
        session.flush()
        for raw in payload.get("screen_devices", []):
            _import_screen_device(session, raw)
        session.flush()
        screen_metric_ids = {app.metric_id for app in session.exec(select(ScreenApp)).all()}
        has_sessions = "screen_sessions" in payload
        for raw in payload.get("entries", []):
            metric = require_metric(session, normalize_slug(_require(raw, "metric")))
            if has_sessions and metric.id in screen_metric_ids:
                continue
            _import_entry(session, raw, metric)
        session.flush()
        if has_sessions:
            for raw in payload.get("screen_sessions", []):
                _import_screen_session(session, raw)
        else:
            _backfill_imported_sessions(session)
        if version >= HABIT_RULES_SCHEMA_VERSION:
            for raw in payload.get("habits", []):
                _import_habit(session, raw)
            session.flush()
            for raw in payload.get("habit_freezes", []):
                _import_habit_freeze(session, raw)
        else:
            today = resolve_today(None)
            for raw in payload.get("habits", []):
                _import_legacy_habit(session, raw, today)
        session.flush()
        # Exports before schema 13 name the Library sections after Entertainment.
        prefix = "library" if version >= LIBRARY_SCHEMA_VERSION else "entertainment"
        for raw in payload.get(f"{prefix}_topics", []):
            _import_library_topic(session, raw)
        session.flush()
        for raw in payload.get(f"{prefix}_titles", []):
            _import_library_title(session, raw)
        for raw in payload.get("sleep_sessions", []):
            _import_sleep_session(session, raw)
        if has_quests:
            quest_ids = import_quests(
                session, {key: payload.get(key, []) for key in QUEST_SECTIONS}
            )
            if version >= SUPPORTS_SCHEMA_VERSION:
                for raw in payload.get("habit_supports", []):
                    _import_habit_support(session, raw, quest_ids)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return ImportSummary(schema_version=version, ignored_sections=ignored)


def _clear_user_data(session: Session) -> None:
    for link in session.exec(select(HabitSupport)).all():
        session.delete(link)
    session.flush()
    clear_quests(session)
    for model in (
        HabitRule,
        HabitMark,
        HabitFreeze,
        SleepSessionStage,
        SleepSession,
        LibraryTitleTopic,
        LibraryTitle,
        LibraryTopic,
        ScreenSession,
        Entry,
        Habit,
        ScreenBudget,
        ScreenApp,
        ScreenDevice,
        ScreenCategory,
        Metric,
    ):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.flush()


# The quest section whose file ids a habit link's `id` refers to, per kind.
_SUPPORT_SECTIONS = {
    "ambition": "ambitions",
    "goal": "goals",
    "milestone": "milestones",
    "side_quest": "side_quests",
    "chapter": "chapters",
    "task": "tasks",
}


def _export_habit_supports(session: Session) -> list[dict[str, Any]]:
    habit_slugs = {habit.id: habit.slug for habit in session.exec(select(Habit)).all()}
    rows: list[dict[str, Any]] = []
    for link in session.exec(select(HabitSupport).order_by(HabitSupport.id)).all():
        kind, item_id = next(
            (kind, getattr(link, column))
            for kind, column in SUPPORT_COLUMNS.items()
            if getattr(link, column) is not None
        )
        rows.append(
            {
                "habit": habit_slugs[link.habit_id],
                "kind": kind.value,
                "id": item_id,
                "created_at": _iso_dt(link.created_at),
            }
        )
    return rows


def _import_habit_support(
    session: Session, raw: dict[str, Any], quest_ids: dict[str, dict[int, int]]
) -> None:
    habit = require_habit(session, normalize_slug(_require(raw, "habit")))
    kind = str(_require(raw, "kind"))
    section = _SUPPORT_SECTIONS.get(kind)
    if section is None:
        raise ValidationError(f"import habit link kind {kind!r} is not a quest item")
    file_id = int(_require(raw, "id"))
    item_id = quest_ids[section].get(file_id)
    if item_id is None:
        raise ValidationError(f"import habit link id {file_id!r} is not in {section}")
    column = getattr(HabitSupport, SUPPORT_COLUMNS[QuestKind(kind)])
    exists = session.exec(
        select(HabitSupport).where(HabitSupport.habit_id == habit.id, column == item_id)
    ).first()
    if exists is None:
        session.add(
            HabitSupport(
                habit_id=habit.id,
                created_at=_parse_datetime(raw.get("created_at")) or datetime.now(UTC),
                **{SUPPORT_COLUMNS[QuestKind(kind)]: item_id},
            )
        )


def _export_metric(metric: Metric) -> dict[str, Any]:
    return {
        "slug": metric.slug,
        "origin": str(metric.origin),
        "name": metric.name,
        "value_type": str(metric.value_type),
        "unit": metric.unit,
        "aggregation": str(metric.aggregation),
        "direction": str(metric.direction),
        "archived_at": _iso_dt(metric.archived_at),
    }


def _export_habit(habit: Habit, rules: list[HabitRule], marks: list[HabitMark]) -> dict[str, Any]:
    return {
        "slug": habit.slug,
        "name": habit.name,
        "time_of_day": str(habit.time_of_day),
        "first_day": habit.first_day.isoformat(),
        "archived_at": _iso_dt(habit.archived_at),
        "rules": [
            {
                "starts_on": rule.starts_on.isoformat(),
                "frequency": str(rule.frequency),
                "weekdays": list(rule.weekdays) if rule.weekdays else None,
                "times": rule.times,
                "check": str(rule.check),
                "source": str(rule.source) if rule.source else None,
                "source_ref": rule.source_ref,
                "threshold": str(rule.threshold) if rule.threshold else None,
                "value": rule.value,
            }
            for rule in rules
        ],
        "marks": [{"day": mark.day.isoformat(), "result": str(mark.result)} for mark in marks],
    }


def _export_habit_freeze(row: HabitFreeze, habit_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "habit": habit_by_id.get(row.habit_id) if row.habit_id is not None else None,
        "start_on": row.start_on.isoformat(),
        "end_on": row.end_on.isoformat(),
        "reason": row.reason,
    }


def _export_entry(entry: Entry, metric_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "metric": metric_by_id[entry.metric_id],
        "occurred_on": entry.occurred_on.isoformat(),
        "occurred_at": _iso_dt(entry.occurred_at),
        "value_num": entry.value_num,
        "value_bool": entry.value_bool,
        "value_text": entry.value_text,
        "note": entry.note,
        "source": str(entry.source),
        "created_at": _iso_dt(entry.created_at),
    }


def _export_screen_category(category: ScreenCategory) -> dict[str, Any]:
    return {
        "slug": category.slug,
        "name": category.name,
        "judgment": str(category.judgment),
        "archived_at": _iso_dt(category.archived_at),
    }


def _export_screen_app(
    app: ScreenApp,
    category_by_id: dict[int | None, str],
    metric_by_id: dict[int | None, str],
) -> dict[str, Any]:
    return {
        "slug": app.slug,
        "name": app.name,
        "category": category_by_id[app.category_id],
        "metric": metric_by_id[app.metric_id],
        "archived_at": _iso_dt(app.archived_at),
    }


def _export_screen_budget(budget: ScreenBudget) -> dict[str, Any]:
    return {
        "slug": budget.slug,
        "name": budget.name,
        "target_kind": str(budget.target_kind),
        "target_slug": budget.target_slug,
        "period": str(budget.period),
        "target_value": budget.target_value,
        "comparator": str(budget.comparator),
        "active_from": budget.active_from.isoformat(),
        "active_to": budget.active_to.isoformat() if budget.active_to is not None else None,
    }


def _export_screen_device(device: ScreenDevice) -> dict[str, Any]:
    return {
        "slug": device.slug,
        "name": device.name,
        "archived_at": _iso_dt(device.archived_at),
        "complete_through": _iso_dt(device.complete_through),
    }


def _export_screen_session(
    row: ScreenSession,
    app_by_id: dict[int | None, str],
    device_by_id: dict[int | None, str],
) -> dict[str, Any]:
    return {
        "app": app_by_id[row.app_id],
        "device": device_by_id.get(row.device_id),
        "started_at": _iso_dt(row.started_at),
        "ended_at": _iso_dt(row.ended_at),
        "minutes": row.minutes,
        "occurred_on": row.occurred_on.isoformat(),
        "note": row.note,
        "source": str(row.source),
        "created_at": _iso_dt(row.created_at),
    }


def _export_sleep_session(row: SleepSession, stages: list[SleepSessionStage]) -> dict[str, Any]:
    return {
        "started_at": _iso_dt(row.started_at),
        "ended_at": _iso_dt(row.ended_at),
        "occurred_on": row.occurred_on.isoformat(),
        "note": row.note,
        "source": str(row.source),
        "created_at": _iso_dt(row.created_at),
        "stages": [
            {
                "stage": str(stage.stage),
                "started_at": _iso_dt(stage.started_at),
                "ended_at": _iso_dt(stage.ended_at),
            }
            for stage in stages
        ],
    }


def _import_sleep_session(session: Session, raw: dict[str, Any]) -> None:
    row = SleepSession(
        started_at=_parse_datetime(_require(raw, "started_at")),
        ended_at=_parse_datetime(_require(raw, "ended_at")),
        occurred_on=_parse_date(_require(raw, "occurred_on")),
        note=raw.get("note"),
        source=Source(raw.get("source", Source.IMPORT)),
        created_at=_parse_datetime(raw.get("created_at")) or datetime.now(UTC),
    )
    session.add(row)
    session.flush()
    for stage in raw.get("stages", []):
        session.add(
            SleepSessionStage(
                session_id=row.id,
                stage=SleepStage(_require(stage, "stage")),
                started_at=_parse_datetime(_require(stage, "started_at")),
                ended_at=_parse_datetime(_require(stage, "ended_at")),
            )
        )


def _export_library_topic(topic: LibraryTopic) -> dict[str, Any]:
    return {
        "slug": topic.slug,
        "name": topic.name,
        "archived_at": _iso_dt(topic.archived_at),
    }


def _export_library_title(title: LibraryTitle, topics: list[str]) -> dict[str, Any]:
    return {
        "slug": title.slug,
        "name": title.name,
        "kind": str(title.kind),
        "creator": title.creator,
        "recommended_by": title.recommended_by,
        "status": str(title.status),
        "started_on": title.started_on.isoformat() if title.started_on is not None else None,
        "finished_on": title.finished_on.isoformat() if title.finished_on is not None else None,
        "progress": title.progress,
        "note": title.note,
        "rating": title.rating,
        "link": title.link,
        "topics": topics,
        "image_url": title.image_url,
        "image_media_type": title.image_media_type if title.image_bytes else None,
        "image_base64": (
            base64.b64encode(title.image_bytes).decode("ascii") if title.image_bytes else None
        ),
        "archived_at": _iso_dt(title.archived_at),
        "created_at": _iso_dt(title.created_at),
    }


def _import_library_topic(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(LibraryTopic).where(LibraryTopic.slug == slug)).first()
    if existing is None:
        existing = LibraryTopic(slug=slug, name=_require(raw, "name"))
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_library_title(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(LibraryTitle).where(LibraryTitle.slug == slug)).first()
    if existing is None:
        existing = LibraryTitle(
            slug=slug,
            name=_require(raw, "name"),
            kind=LibraryKind(_require(raw, "kind")),
        )
        session.add(existing)
        session.flush()
    existing.name = raw.get("name", existing.name)
    existing.kind = LibraryKind(raw.get("kind", existing.kind))
    existing.creator = raw.get("creator")
    existing.recommended_by = raw.get("recommended_by")
    existing.status = LibraryStatus(raw.get("status", existing.status))
    started_on = raw.get("started_on")
    existing.started_on = _parse_date(started_on) if started_on else None
    finished_on = raw.get("finished_on")
    existing.finished_on = _parse_date(finished_on) if finished_on else None
    existing.progress = raw.get("progress")
    existing.note = raw.get("note")
    existing.rating = raw.get("rating")
    existing.link = raw.get("link")
    existing.archived_at = _parse_datetime(raw.get("archived_at"))
    created_at = _parse_datetime(raw.get("created_at"))
    if created_at is not None:
        existing.created_at = created_at
    image_base64 = raw.get("image_base64")
    if image_base64:
        existing.image_bytes = base64.b64decode(image_base64)
        existing.image_media_type = raw.get("image_media_type") or "image/jpeg"
        existing.image_url = None
    else:
        existing.image_bytes = None
        existing.image_media_type = None
        existing.image_url = raw.get("image_url")
    session.flush()
    _import_title_topics(session, existing, raw.get("topics") or [])


def _import_title_topics(session: Session, title: LibraryTitle, slugs: list[Any]) -> None:
    existing = list(
        session.exec(select(LibraryTitleTopic).where(LibraryTitleTopic.title_id == title.id)).all()
    )
    for link in existing:
        session.delete(link)
    session.flush()
    seen: set[str] = set()
    for raw_slug in slugs:
        slug = normalize_slug(str(raw_slug))
        if slug in seen:
            continue
        seen.add(slug)
        topic = require_library_topic(session, slug)
        session.add(LibraryTitleTopic(title_id=title.id, topic_id=topic.id))


def _metric_origin(raw: dict[str, Any], slug: str) -> MetricOrigin:
    """The origin a metric is imported with. Exports from before schema 12 carry an `area`
    instead: the internal habits and screen areas, and the journal metric, map onto origins."""
    if "origin" in raw:
        return MetricOrigin(raw["origin"])
    if slug == _JOURNAL_METRIC_SLUG:
        return MetricOrigin.JOURNAL
    return _ORIGIN_BY_LEGACY_AREA.get(raw.get("area", ""), MetricOrigin.MANUAL)


def _import_metric(
    session: Session, raw: dict[str, Any], archived_areas: dict[str, datetime | None]
) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    origin = _metric_origin(raw, slug)
    existing = session.exec(select(Metric).where(Metric.slug == slug)).first()
    if existing is None:
        existing = Metric(
            slug=slug,
            name=_require(raw, "name"),
            value_type=ValueType(_require(raw, "value_type")),
            aggregation=Aggregation(_require(raw, "aggregation")),
            direction=Direction(raw.get("direction", Direction.NEUTRAL)),
        )
        session.add(existing)
    existing.origin = origin
    existing.name = raw.get("name", existing.name)
    existing.value_type = ValueType(raw.get("value_type", existing.value_type))
    existing.unit = raw.get("unit")
    existing.aggregation = Aggregation(raw.get("aggregation", existing.aggregation))
    existing.direction = Direction(raw.get("direction", existing.direction))
    # A metric in an archived area counted as archived, so it stays that way without the area.
    existing.archived_at = _parse_datetime(raw.get("archived_at")) or archived_areas.get(
        raw.get("area", "")
    )


def _import_habit(session: Session, raw: dict[str, Any]) -> None:
    """A schema 15+ habit: replaces a habit with the same slug, with its rules and answers."""
    slug = normalize_slug(_require(raw, "slug"))
    first_day = _parse_date(_require(raw, "first_day"))
    habit = session.exec(select(Habit).where(Habit.slug == slug)).first()
    if habit is None:
        habit = Habit(slug=slug, name=_require(raw, "name"), first_day=first_day)
        session.add(habit)
    habit.name = raw.get("name", habit.name)
    habit.first_day = first_day
    habit.time_of_day = TimeOfDay(raw.get("time_of_day") or TimeOfDay.ANYTIME)
    habit.archived_at = _parse_datetime(raw.get("archived_at"))
    session.flush()
    for model in (HabitRule, HabitMark):
        for row in session.exec(select(model).where(model.habit_id == habit.id)).all():
            session.delete(row)
    session.flush()
    rules = raw.get("rules") or []
    if not rules:
        raise ValidationError(f"import habit {slug!r} has no rules")
    for item in rules:
        source = item.get("source")
        threshold = item.get("threshold")
        session.add(
            HabitRule(
                habit_id=habit.id,
                starts_on=_parse_date(_require(item, "starts_on")),
                frequency=HabitFrequency(_require(item, "frequency")),
                weekdays=item.get("weekdays") or None,
                times=item.get("times"),
                check=HabitCheck(_require(item, "check")),
                source=HabitSource(source) if source else None,
                source_ref=item.get("source_ref"),
                threshold=HabitThreshold(threshold) if threshold else None,
                value=item.get("value"),
            )
        )
    for item in raw.get("marks") or []:
        session.add(
            HabitMark(
                habit_id=habit.id,
                day=_parse_date(_require(item, "day")),
                result=HabitMarkResult(_require(item, "result")),
            )
        )


def _import_habit_freeze(session: Session, raw: dict[str, Any]) -> None:
    habit_slug = raw.get("habit")
    habit_id = require_habit(session, normalize_slug(habit_slug)).id if habit_slug else None
    start_on = _parse_date(_require(raw, "start_on"))
    end_on = _parse_date(_require(raw, "end_on"))
    same = session.exec(
        select(HabitFreeze).where(
            HabitFreeze.habit_id == habit_id,
            HabitFreeze.start_on == start_on,
            HabitFreeze.end_on == end_on,
        )
    ).first()
    if same is None:
        session.add(
            HabitFreeze(
                habit_id=habit_id, start_on=start_on, end_on=end_on, reason=raw.get("reason")
            )
        )


def _import_legacy_habit(session: Session, raw: dict[str, Any], today: date) -> None:
    """A habit from an export before schema 15, converted as the schema 15 migration does:
    its schedule becomes the first rule, its past becomes Done marks, its skips and pauses
    become freezes, and the metric it read is archived unless it backs a screen app."""
    slug = normalize_slug(_require(raw, "slug"))
    metric = require_metric(session, normalize_slug(_require(raw, "metric")))
    app = session.exec(select(ScreenApp).where(ScreenApp.metric_id == metric.id)).first()
    breaks = [
        (_parse_date(_require(item, "start_on")), _parse_date(_require(item, "end_on")), item)
        for item in raw.get("breaks") or []
    ]
    active_to = raw.get("active_to")
    kind = raw.get("kind") or _legacy_habit_kind(metric)
    legacy = LegacyHabit(
        kind=str(kind),
        period=Period(_require(raw, "period")),
        comparator=Comparator(_require(raw, "comparator")),
        target_value=float(_require(raw, "target_value")),
        active_from=_parse_date(_require(raw, "active_from")),
        active_to=_parse_date(active_to) if active_to else None,
        aggregation=Aggregation(metric.aggregation),
        weekdays=frozenset(raw["weekdays"]) if raw.get("weekdays") else None,
        breaks=tuple((start, end) for start, end, _ in breaks),
        screen_app_slug=app.slug if app is not None else None,
    )
    entries = [
        EntryView(occurred_on=row.occurred_on, value_num=row.value_num, value_bool=row.value_bool)
        for row in session.exec(select(Entry).where(Entry.metric_id == metric.id)).all()
    ]
    converted = convert_legacy_habit(legacy, entries, today)
    rule = converted.rule
    archived_at = _parse_datetime(raw.get("archived_at"))
    if archived_at is None and legacy.active_to is not None and legacy.active_to < today:
        archived_at = datetime.combine(legacy.active_to, time(23, 59), tzinfo=UTC)
    _import_habit(
        session,
        {
            "slug": slug,
            "name": _require(raw, "name"),
            "time_of_day": raw.get("time_of_day"),
            "first_day": legacy.active_from.isoformat(),
            "archived_at": _iso_dt(archived_at),
            "rules": [
                {
                    "starts_on": legacy.active_from.isoformat(),
                    "frequency": rule.frequency,
                    "weekdays": list(rule.weekdays) if rule.weekdays else None,
                    "times": rule.times,
                    "check": rule.check,
                    "source": rule.source,
                    "source_ref": rule.source_ref,
                    "threshold": rule.threshold,
                    "value": rule.value,
                }
            ],
            "marks": [
                {"day": day.isoformat(), "result": HabitMarkResult.DONE}
                for day in converted.done_days
            ],
        },
    )
    session.flush()
    for start_on, end_on, item in breaks:
        _import_habit_freeze(
            session,
            {
                "habit": slug,
                "start_on": start_on.isoformat(),
                "end_on": end_on.isoformat(),
                "reason": item.get("note"),
            },
        )
    origin = MetricOrigin(metric.origin)
    if app is None and metric.archived_at is None and origin in _HABIT_READ_ORIGINS:
        metric.archived_at = datetime.now(UTC)
        session.add(metric)


_HABIT_READ_ORIGINS = (MetricOrigin.MANUAL, MetricOrigin.HABIT)


def _legacy_habit_kind(metric: Metric) -> str:
    value_type = ValueType(metric.value_type)
    if value_type is ValueType.BOOL:
        return "check"
    if value_type is ValueType.DURATION:
        return "duration"
    return "count"


def _import_screen_category(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(ScreenCategory).where(ScreenCategory.slug == slug)).first()
    if existing is None:
        existing = ScreenCategory(
            slug=slug,
            name=_require(raw, "name"),
            judgment=ScreenJudgment(_require(raw, "judgment")),
        )
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.judgment = ScreenJudgment(raw.get("judgment", existing.judgment))
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_screen_app(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    category = require_screen_category(session, normalize_slug(_require(raw, "category")))
    metric = require_metric(session, normalize_slug(_require(raw, "metric")))
    existing = session.exec(select(ScreenApp).where(ScreenApp.slug == slug)).first()
    if existing is None:
        existing = ScreenApp(
            slug=slug,
            name=_require(raw, "name"),
            category_id=category.id,
            metric_id=metric.id,
        )
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.category_id = category.id
    existing.metric_id = metric.id
    metric.origin = MetricOrigin.SCREEN
    session.add(metric)
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_screen_budget(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(ScreenBudget).where(ScreenBudget.slug == slug)).first()
    if existing is None:
        existing = ScreenBudget(
            slug=slug,
            name=_require(raw, "name"),
            target_kind=ScreenBudgetTargetKind(_require(raw, "target_kind")),
            target_slug=_require(raw, "target_slug"),
            period=Period(_require(raw, "period")),
            target_value=float(_require(raw, "target_value")),
            comparator=Comparator(_require(raw, "comparator")),
            active_from=_parse_date(_require(raw, "active_from")),
        )
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.target_kind = ScreenBudgetTargetKind(raw.get("target_kind", existing.target_kind))
    existing.target_slug = raw.get("target_slug", existing.target_slug)
    existing.period = Period(raw.get("period", existing.period))
    existing.target_value = float(raw.get("target_value", existing.target_value))
    existing.comparator = Comparator(raw.get("comparator", existing.comparator))
    existing.active_from = _parse_date(raw.get("active_from", existing.active_from.isoformat()))
    active_to = raw.get("active_to")
    existing.active_to = _parse_date(active_to) if active_to else None


def _import_screen_device(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(ScreenDevice).where(ScreenDevice.slug == slug)).first()
    if existing is None:
        existing = ScreenDevice(slug=slug, name=_require(raw, "name"))
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.archived_at = _parse_datetime(raw.get("archived_at"))
    existing.complete_through = _parse_datetime(raw.get("complete_through"))


def _import_screen_session(session: Session, raw: dict[str, Any]) -> None:
    app = require_screen_app(session, normalize_slug(_require(raw, "app")))
    device_slug = raw.get("device")
    device_id = (
        require_screen_device(session, normalize_slug(device_slug)).id if device_slug else None
    )
    metric = require_metric(session, app.slug)
    created_at = _parse_datetime(raw.get("created_at")) or datetime.now(UTC)
    started_at = _parse_datetime(raw.get("started_at"))
    ended_at = _parse_datetime(raw.get("ended_at"))
    minutes = float(_require(raw, "minutes"))
    occurred_on = _parse_date(_require(raw, "occurred_on"))
    entry = Entry(
        metric_id=metric.id,
        occurred_on=occurred_on,
        occurred_at=started_at,
        value_num=minutes,
        note=raw.get("note"),
        source=Source(raw.get("source", Source.IMPORT)),
        created_at=created_at,
    )
    session.add(entry)
    session.flush()
    session.add(
        ScreenSession(
            app_id=app.id,
            device_id=device_id,
            started_at=started_at,
            ended_at=ended_at,
            minutes=minutes,
            occurred_on=occurred_on,
            note=raw.get("note"),
            source=Source(raw.get("source", Source.IMPORT)),
            created_at=created_at,
            entry_id=entry.id,
        )
    )


def _backfill_imported_sessions(session: Session) -> None:
    apps = list(session.exec(select(ScreenApp)).all())
    metric_to_app = {app.metric_id: app for app in apps}
    if not metric_to_app:
        return
    linked = {
        row.entry_id
        for row in session.exec(select(ScreenSession)).all()
        if row.entry_id is not None
    }
    for entry in session.exec(select(Entry)).all():
        if entry.id in linked or entry.metric_id not in metric_to_app:
            continue
        if entry.value_num is None or entry.value_num <= 0:
            continue
        app = metric_to_app[entry.metric_id]
        session.add(
            ScreenSession(
                app_id=app.id,
                minutes=entry.value_num,
                occurred_on=entry.occurred_on,
                note=entry.note,
                source=entry.source,
                created_at=entry.created_at,
                entry_id=entry.id,
            )
        )


def _import_entry(session: Session, raw: dict[str, Any], metric: Metric | None = None) -> Entry:
    if metric is None:
        metric = require_metric(session, normalize_slug(_require(raw, "metric")))
    created_at = _parse_datetime(raw.get("created_at")) or datetime.now(UTC)
    entry = Entry(
        metric_id=metric.id,
        occurred_on=_parse_date(_require(raw, "occurred_on")),
        occurred_at=_parse_datetime(raw.get("occurred_at")),
        value_num=raw.get("value_num"),
        value_bool=raw.get("value_bool"),
        value_text=raw.get("value_text"),
        note=raw.get("note"),
        source=Source(raw.get("source", Source.IMPORT)),
        created_at=created_at,
    )
    session.add(entry)
    session.flush()
    return entry


def _require(raw: dict[str, Any], key: str) -> Any:
    if key not in raw or raw[key] is None or raw[key] == "":
        raise ValidationError(f"import is missing required field {key!r}")
    return raw[key]


def _iso_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_datetime(raw: str | datetime | None) -> datetime | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        value = raw
    else:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_date(raw: str | date) -> date:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(raw)
