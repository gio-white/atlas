import base64
from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from atlas.db import CURRENT_SCHEMA_VERSION
from atlas.db.models import (
    Area,
    EntertainmentTitle,
    EntertainmentTitleTopic,
    EntertainmentTopic,
    Entry,
    Goal,
    Habit,
    Metric,
    Milestone,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    ScreenDevice,
    ScreenSession,
    Task,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    EntertainmentKind,
    EntertainmentStatus,
    GoalHorizon,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    ScreenBudgetTargetKind,
    ScreenJudgment,
    Source,
    TaskBucket,
    TaskPriority,
    ValueType,
    infer_horizon,
    parent_horizon_is_valid,
)
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    require_area,
    require_entertainment_topic,
    require_goal,
    require_metric,
    require_screen_app,
    require_screen_category,
    require_screen_device,
)
from atlas.services.slugs import normalize_slug


def export_all(session: Session) -> dict[str, Any]:
    areas = list(session.exec(select(Area).order_by(Area.slug)).all())
    metrics = list(session.exec(select(Metric).order_by(Metric.slug)).all())
    habits = list(session.exec(select(Habit).order_by(Habit.slug)).all())
    goals = list(session.exec(select(Goal).order_by(Goal.slug)).all())
    milestones = list(session.exec(select(Milestone).order_by(Milestone.id)).all())
    screen_categories = list(
        session.exec(select(ScreenCategory).order_by(ScreenCategory.slug)).all()
    )
    screen_apps = list(session.exec(select(ScreenApp).order_by(ScreenApp.slug)).all())
    screen_budgets = list(session.exec(select(ScreenBudget).order_by(ScreenBudget.slug)).all())
    screen_devices = list(session.exec(select(ScreenDevice).order_by(ScreenDevice.slug)).all())
    screen_sessions = list(session.exec(select(ScreenSession).order_by(ScreenSession.id)).all())
    entertainment_topics = list(
        session.exec(select(EntertainmentTopic).order_by(EntertainmentTopic.slug)).all()
    )
    entertainment_titles = list(
        session.exec(select(EntertainmentTitle).order_by(EntertainmentTitle.slug)).all()
    )
    entertainment_links = list(session.exec(select(EntertainmentTitleTopic)).all())
    tasks = list(session.exec(select(Task).order_by(Task.id)).all())
    entries = list(session.exec(select(Entry).order_by(Entry.occurred_on, Entry.id)).all())

    area_by_id = {area.id: area.slug for area in areas}
    metric_by_id = {metric.id: metric.slug for metric in metrics}
    goal_by_id = {goal.id: goal.slug for goal in goals}
    category_by_id = {category.id: category.slug for category in screen_categories}
    device_by_id = {device.id: device.slug for device in screen_devices}
    app_by_id = {app.id: app.slug for app in screen_apps}
    topic_by_id = {topic.id: topic.slug for topic in entertainment_topics}
    topics_by_title: dict[int | None, list[str]] = {}
    for link in entertainment_links:
        slug = topic_by_id.get(link.topic_id)
        if slug is None:
            continue
        topics_by_title.setdefault(link.title_id, []).append(slug)
    for slugs in topics_by_title.values():
        slugs.sort()

    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "areas": [_export_area(area) for area in areas],
        "metrics": [_export_metric(metric, area_by_id) for metric in metrics],
        "habits": [_export_habit(habit, metric_by_id) for habit in habits],
        "goals": [_export_goal(goal, area_by_id, metric_by_id, goal_by_id) for goal in goals],
        "milestones": [_export_milestone(row, goal_by_id) for row in milestones],
        "screen_categories": [_export_screen_category(row) for row in screen_categories],
        "screen_apps": [
            _export_screen_app(row, category_by_id, metric_by_id) for row in screen_apps
        ],
        "screen_budgets": [_export_screen_budget(row) for row in screen_budgets],
        "screen_devices": [_export_screen_device(row) for row in screen_devices],
        "screen_sessions": [
            _export_screen_session(row, app_by_id, device_by_id) for row in screen_sessions
        ],
        "entertainment_topics": [_export_entertainment_topic(row) for row in entertainment_topics],
        "entertainment_titles": [
            _export_entertainment_title(row, topics_by_title.get(row.id, []))
            for row in entertainment_titles
        ],
        "tasks": [_export_task(task, goal_by_id) for task in tasks],
        "entries": [_export_entry(entry, metric_by_id) for entry in entries],
    }


def import_all(session: Session, payload: dict[str, Any], *, replace: bool = False) -> None:
    version = payload.get("schema_version")
    if version not in set(range(1, CURRENT_SCHEMA_VERSION + 1)):
        raise ValidationError(
            f"unsupported export schema_version {version!r}; "
            f"expected 1 through {CURRENT_SCHEMA_VERSION}"
        )
    try:
        if replace:
            _clear_user_data(session)
        for raw in payload.get("areas", []):
            _import_area(session, raw)
        session.flush()
        for raw in payload.get("metrics", []):
            _import_metric(session, raw)
        session.flush()
        for raw in payload.get("habits", []):
            _import_habit(session, raw)
        session.flush()
        for raw in payload.get("goals", []):
            _import_goal(session, raw)
        session.flush()
        for raw in payload.get("goals", []):
            _import_goal_parent(session, raw)
        session.flush()
        for raw in payload.get("milestones", []):
            _import_milestone(session, raw)
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
        for raw in payload.get("tasks", []):
            _import_task(session, raw)
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
        for raw in payload.get("entertainment_topics", []):
            _import_entertainment_topic(session, raw)
        session.flush()
        for raw in payload.get("entertainment_titles", []):
            _import_entertainment_title(session, raw)
        session.commit()
    except Exception:
        session.rollback()
        raise


def _clear_user_data(session: Session) -> None:
    for goal in session.exec(select(Goal)).all():
        goal.parent_id = None
        session.add(goal)
    session.flush()
    for model in (
        EntertainmentTitleTopic,
        EntertainmentTitle,
        EntertainmentTopic,
        ScreenSession,
        Entry,
        Milestone,
        Habit,
        Task,
        Goal,
        ScreenBudget,
        ScreenApp,
        ScreenDevice,
        ScreenCategory,
        Metric,
        Area,
    ):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.flush()


def _export_area(area: Area) -> dict[str, Any]:
    return {
        "slug": area.slug,
        "name": area.name,
        "description": area.description,
        "archived_at": _iso_dt(area.archived_at),
    }


def _export_metric(metric: Metric, area_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "slug": metric.slug,
        "area": area_by_id[metric.area_id],
        "name": metric.name,
        "value_type": str(metric.value_type),
        "unit": metric.unit,
        "aggregation": str(metric.aggregation),
        "direction": str(metric.direction),
        "archived_at": _iso_dt(metric.archived_at),
    }


def _export_habit(habit: Habit, metric_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "slug": habit.slug,
        "metric": metric_by_id[habit.metric_id],
        "name": habit.name,
        "period": str(habit.period),
        "target_value": habit.target_value,
        "comparator": str(habit.comparator),
        "weekdays": list(habit.weekdays) if habit.weekdays is not None else None,
        "active_from": habit.active_from.isoformat(),
        "active_to": habit.active_to.isoformat() if habit.active_to is not None else None,
    }


def _export_goal(
    goal: Goal,
    area_by_id: dict[int | None, str],
    metric_by_id: dict[int | None, str],
    goal_by_id: dict[int | None, str],
) -> dict[str, Any]:
    return {
        "slug": goal.slug,
        "area": area_by_id.get(goal.area_id) if goal.area_id is not None else None,
        "name": goal.name,
        "kind": str(goal.kind),
        "metric": metric_by_id.get(goal.metric_id),
        "target_value": goal.target_value,
        "comparator": str(goal.comparator) if goal.comparator is not None else None,
        "baseline_value": goal.baseline_value,
        "measure": str(goal.measure) if goal.measure is not None else None,
        "start_on": goal.start_on.isoformat(),
        "due_on": goal.due_on.isoformat(),
        "horizon": str(goal.horizon),
        "parent": goal_by_id.get(goal.parent_id),
        "description": goal.description,
        "status": str(goal.status),
        "achieved_at": _iso_dt(goal.achieved_at),
    }


def _export_milestone(milestone: Milestone, goal_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "goal": goal_by_id[milestone.goal_id],
        "name": milestone.name,
        "due_on": milestone.due_on.isoformat() if milestone.due_on is not None else None,
        "done_at": _iso_dt(milestone.done_at),
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


def _export_entertainment_topic(topic: EntertainmentTopic) -> dict[str, Any]:
    return {
        "slug": topic.slug,
        "name": topic.name,
        "archived_at": _iso_dt(topic.archived_at),
    }


def _export_entertainment_title(title: EntertainmentTitle, topics: list[str]) -> dict[str, Any]:
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
        "topics": topics,
        "image_url": title.image_url,
        "image_media_type": title.image_media_type if title.image_bytes else None,
        "image_base64": (
            base64.b64encode(title.image_bytes).decode("ascii") if title.image_bytes else None
        ),
        "archived_at": _iso_dt(title.archived_at),
        "created_at": _iso_dt(title.created_at),
    }


def _import_entertainment_topic(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(
        select(EntertainmentTopic).where(EntertainmentTopic.slug == slug)
    ).first()
    if existing is None:
        existing = EntertainmentTopic(slug=slug, name=_require(raw, "name"))
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_entertainment_title(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(
        select(EntertainmentTitle).where(EntertainmentTitle.slug == slug)
    ).first()
    if existing is None:
        existing = EntertainmentTitle(
            slug=slug,
            name=_require(raw, "name"),
            kind=EntertainmentKind(_require(raw, "kind")),
        )
        session.add(existing)
        session.flush()
    existing.name = raw.get("name", existing.name)
    existing.kind = EntertainmentKind(raw.get("kind", existing.kind))
    existing.creator = raw.get("creator")
    existing.recommended_by = raw.get("recommended_by")
    existing.status = EntertainmentStatus(raw.get("status", existing.status))
    started_on = raw.get("started_on")
    existing.started_on = _parse_date(started_on) if started_on else None
    finished_on = raw.get("finished_on")
    existing.finished_on = _parse_date(finished_on) if finished_on else None
    existing.progress = raw.get("progress")
    existing.note = raw.get("note")
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


def _import_title_topics(session: Session, title: EntertainmentTitle, slugs: list[Any]) -> None:
    existing = list(
        session.exec(
            select(EntertainmentTitleTopic).where(EntertainmentTitleTopic.title_id == title.id)
        ).all()
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
        topic = require_entertainment_topic(session, slug)
        session.add(EntertainmentTitleTopic(title_id=title.id, topic_id=topic.id))


def _import_area(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    existing = session.exec(select(Area).where(Area.slug == slug)).first()
    if existing is None:
        existing = Area(slug=slug, name=_require(raw, "name"))
        session.add(existing)
    existing.name = raw.get("name", existing.name)
    existing.description = raw.get("description")
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_metric(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    area = require_area(session, normalize_slug(_require(raw, "area")))
    existing = session.exec(select(Metric).where(Metric.slug == slug)).first()
    if existing is None:
        existing = Metric(
            slug=slug,
            area_id=area.id,
            name=_require(raw, "name"),
            value_type=ValueType(_require(raw, "value_type")),
            aggregation=Aggregation(_require(raw, "aggregation")),
            direction=Direction(raw.get("direction", Direction.NEUTRAL)),
        )
        session.add(existing)
    existing.area_id = area.id
    existing.name = raw.get("name", existing.name)
    existing.value_type = ValueType(raw.get("value_type", existing.value_type))
    existing.unit = raw.get("unit")
    existing.aggregation = Aggregation(raw.get("aggregation", existing.aggregation))
    existing.direction = Direction(raw.get("direction", existing.direction))
    existing.archived_at = _parse_datetime(raw.get("archived_at"))


def _import_habit(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    metric = require_metric(session, normalize_slug(_require(raw, "metric")))
    existing = session.exec(select(Habit).where(Habit.slug == slug)).first()
    if existing is None:
        existing = Habit(
            slug=slug,
            metric_id=metric.id,
            name=_require(raw, "name"),
            period=Period(_require(raw, "period")),
            target_value=float(_require(raw, "target_value")),
            comparator=Comparator(_require(raw, "comparator")),
            active_from=_parse_date(_require(raw, "active_from")),
        )
        session.add(existing)
    existing.metric_id = metric.id
    existing.name = raw.get("name", existing.name)
    existing.period = Period(raw.get("period", existing.period))
    existing.target_value = float(raw.get("target_value", existing.target_value))
    existing.comparator = Comparator(raw.get("comparator", existing.comparator))
    existing.weekdays = raw.get("weekdays")
    existing.active_from = _parse_date(raw.get("active_from", existing.active_from.isoformat()))
    active_to = raw.get("active_to")
    existing.active_to = _parse_date(active_to) if active_to else None


def _import_goal(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    area_raw = raw.get("area")
    area_id = require_area(session, normalize_slug(area_raw)).id if area_raw else None
    metric_slug = raw.get("metric")
    metric_id = require_metric(session, normalize_slug(metric_slug)).id if metric_slug else None
    existing = session.exec(select(Goal).where(Goal.slug == slug)).first()
    if existing is None:
        existing = Goal(
            slug=slug,
            area_id=area_id,
            name=_require(raw, "name"),
            kind=GoalKind(_require(raw, "kind")),
            start_on=_parse_date(_require(raw, "start_on")),
            due_on=_parse_date(_require(raw, "due_on")),
        )
        session.add(existing)
    existing.area_id = area_id
    existing.name = raw.get("name", existing.name)
    existing.kind = GoalKind(raw.get("kind", existing.kind))
    existing.metric_id = metric_id
    existing.target_value = raw.get("target_value")
    comparator = raw.get("comparator")
    existing.comparator = Comparator(comparator) if comparator else None
    existing.baseline_value = raw.get("baseline_value")
    measure = raw.get("measure")
    existing.measure = Measure(measure) if measure else None
    existing.start_on = _parse_date(raw.get("start_on", existing.start_on.isoformat()))
    existing.due_on = _parse_date(raw.get("due_on", existing.due_on.isoformat()))
    horizon = raw.get("horizon")
    if horizon:
        existing.horizon = GoalHorizon(horizon)
    else:
        existing.horizon = infer_horizon(existing.start_on, existing.due_on)
    existing.description = raw.get("description")
    existing.status = GoalStatus(raw.get("status", existing.status))
    existing.achieved_at = _parse_datetime(raw.get("achieved_at"))


def _import_goal_parent(session: Session, raw: dict[str, Any]) -> None:
    slug = normalize_slug(_require(raw, "slug"))
    goal = require_goal(session, slug)
    parent_slug = raw.get("parent")
    if not parent_slug:
        goal.parent_id = None
        return
    parent = require_goal(session, normalize_slug(parent_slug))
    child_horizon = GoalHorizon(goal.horizon)
    parent_horizon = GoalHorizon(parent.horizon)
    if not parent_horizon_is_valid(child_horizon, parent_horizon):
        raise ValidationError(f"goal {slug!r} cannot parent under {parent.slug!r}")
    if parent.id == goal.id:
        raise ValidationError("a goal cannot be its own parent")
    goal.parent_id = parent.id


def _import_milestone(session: Session, raw: dict[str, Any]) -> None:
    goal = require_goal(session, normalize_slug(_require(raw, "goal")))
    name = _require(raw, "name")
    existing = next(
        (
            row
            for row in session.exec(select(Milestone).where(Milestone.goal_id == goal.id)).all()
            if row.name == name
        ),
        None,
    )
    due_on = raw.get("due_on")
    if existing is None:
        existing = Milestone(goal_id=goal.id, name=name)
        session.add(existing)
    existing.due_on = _parse_date(due_on) if due_on else None
    existing.done_at = _parse_datetime(raw.get("done_at"))


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


def _export_task(task: Task, goal_by_id: dict[int | None, str]) -> dict[str, Any]:
    return {
        "title": task.title,
        "bucket": str(task.bucket),
        "due_on": task.due_on.isoformat() if task.due_on is not None else None,
        "due_at": _iso_dt(task.due_at),
        "priority": str(task.priority),
        "goal": goal_by_id.get(task.goal_id),
        "done_at": _iso_dt(task.done_at),
        "created_at": _iso_dt(task.created_at),
    }


def _import_task(session: Session, raw: dict[str, Any]) -> None:
    created_at = _parse_datetime(raw.get("created_at")) or datetime.now(UTC)
    due_on = raw.get("due_on")
    goal_slug = raw.get("goal")
    goal_id = require_goal(session, normalize_slug(goal_slug)).id if goal_slug else None
    session.add(
        Task(
            title=_require(raw, "title"),
            bucket=TaskBucket(_require(raw, "bucket")),
            due_on=_parse_date(due_on) if due_on else None,
            due_at=_parse_datetime(raw.get("due_at")),
            priority=TaskPriority(raw.get("priority", TaskPriority.NORMAL)),
            goal_id=goal_id,
            done_at=_parse_datetime(raw.get("done_at")),
            created_at=created_at,
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
