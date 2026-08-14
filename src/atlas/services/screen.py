from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlmodel import Session, select

from atlas.db.models import (
    Area,
    Entry,
    Metric,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    ScreenDevice,
    ScreenSession,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Period,
    ScreenAppSpec,
    ScreenBudgetSpec,
    ScreenBudgetTargetKind,
    ScreenCategorySpec,
    ScreenInsightKind,
    ScreenJudgment,
    ScreenScoreBand,
    ScreenSessionView,
    Source,
    ValueType,
    add_minutes,
    adherence,
    attributed_day_minutes,
    bucket_for,
    current_streak,
    direction_for_judgment,
    is_satisfied,
    is_scheduled,
    longest_streak,
    member_apps,
    minutes_in_range,
    resolve_screen_session,
    rollup,
    screen_dashboard_math,
    session_entry_views,
)
from atlas.domain.screen import (
    ScreenAppShare,
    ScreenCategoryShare,
    ScreenComparisonPoint,
    ScreenDayBar,
    ScreenDeviceShare,
    ScreenInsight,
    ScreenLongestDay,
    ScreenTrendPoint,
)
from atlas.services.clock import resolve_today
from atlas.services.entries import log_entry
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    metric_by_id,
    not_archived,
    require_entry,
    require_screen_app,
    require_screen_budget,
    require_screen_category,
    require_screen_device,
    require_screen_session,
)
from atlas.services.slugs import display_name, normalize_slug
from atlas.settings import load_settings

SCREEN_AREA_SLUG = "screen"
_UNSET = object()


@dataclass(frozen=True, slots=True)
class ScreenAppRow:
    slug: str
    name: str
    category: str
    metric: str
    minutes: float | None
    archived_at: datetime | None


@dataclass(frozen=True, slots=True)
class ScreenCategoryRow:
    slug: str
    name: str
    judgment: ScreenJudgment
    minutes: float | None
    apps: list[ScreenAppRow]
    archived_at: datetime | None


@dataclass(frozen=True, slots=True)
class ScreenJudgmentTotals:
    useful: float | None
    waste: float | None
    neutral: float | None
    total: float | None


@dataclass(frozen=True, slots=True)
class ScreenSessionRow:
    id: int
    app: str
    category: str
    metric: str
    occurred_on: date
    minutes: float | None
    note: str | None


@dataclass(frozen=True, slots=True)
class ScreenBudgetStatus:
    slug: str
    name: str
    target_kind: ScreenBudgetTargetKind
    target_slug: str
    period: Period
    target_value: float
    comparator: Comparator
    current_value: float | None
    satisfied: bool
    scheduled: bool
    current_streak: int
    longest_streak: int
    adherence: float | None
    as_of: date


@dataclass(frozen=True, slots=True)
class ScreenView:
    as_of: date
    categories: list[ScreenCategoryRow]
    judgments: ScreenJudgmentTotals
    sessions: list[ScreenSessionRow]
    budgets: list[ScreenBudgetStatus]


@dataclass(frozen=True, slots=True)
class ScreenDashboard:
    period: Period
    as_of: date
    range_start: date
    range_end: date
    previous_start: date
    previous_end: date
    total: float | None
    daily_average: float | None
    longest_day: ScreenLongestDay | None
    delta_minutes: float | None
    delta_fraction: float | None
    score: int | None
    score_band: ScreenScoreBand | None
    judgments: ScreenJudgmentTotals
    apps: list[ScreenAppShare]
    categories: list[ScreenCategoryShare]
    devices: list[ScreenDeviceShare]
    daily: list[ScreenDayBar]
    comparison: list[ScreenComparisonPoint]
    hours: list[list[float]]
    trend: list[ScreenTrendPoint]
    insights: list[ScreenInsight]
    budgets: list[ScreenBudgetStatus]


def create_screen_category(
    session: Session,
    slug: str,
    *,
    judgment: ScreenJudgment,
    name: str | None = None,
) -> ScreenCategory:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, ScreenCategory, slug)
    judgment = ScreenJudgment(judgment)
    _ensure_screen_area(session)
    category = ScreenCategory(
        slug=slug,
        name=name if name is not None else display_name(slug),
        judgment=judgment,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_screen_categories(
    session: Session,
    *,
    include_archived: bool = False,
) -> list[ScreenCategory]:
    statement = select(ScreenCategory).order_by(ScreenCategory.slug)
    if not include_archived:
        statement = statement.where(not_archived(ScreenCategory.archived_at))
    return list(session.exec(statement).all())


def get_screen_category(session: Session, slug: str) -> ScreenCategory:
    return require_screen_category(session, normalize_slug(slug))


def update_screen_category(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    judgment: ScreenJudgment | None = None,
) -> ScreenCategory:
    category = require_screen_category(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        category.name = name
    if judgment is not None:
        judgment = ScreenJudgment(judgment)
        category.judgment = judgment
        direction = direction_for_judgment(judgment)
        for app in _apps_for_category(session, category.id):
            metric = metric_by_id(session, app.metric_id)
            metric.direction = direction
            session.add(metric)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def create_screen_app(
    session: Session,
    slug: str,
    *,
    category_slug: str,
    name: str | None = None,
) -> ScreenApp:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, ScreenApp, slug)
    ensure_unique_slug(session, Metric, slug)
    category = require_screen_category(session, normalize_slug(category_slug))
    if category.archived_at is not None:
        raise ValidationError(f"screen_category {category.slug!r} is archived")
    area = _ensure_screen_area(session)
    display = name if name is not None else display_name(slug)
    metric = Metric(
        area_id=area.id,
        slug=slug,
        name=display,
        value_type=ValueType.DURATION,
        unit="min",
        aggregation=Aggregation.SUM,
        direction=direction_for_judgment(ScreenJudgment(category.judgment)),
    )
    session.add(metric)
    session.flush()
    app = ScreenApp(
        slug=slug,
        name=display,
        category_id=category.id,
        metric_id=metric.id,
    )
    session.add(app)
    session.commit()
    session.refresh(app)
    return app


def list_screen_apps(session: Session, *, include_archived: bool = False) -> list[ScreenApp]:
    statement = select(ScreenApp).order_by(ScreenApp.slug)
    if not include_archived:
        statement = statement.where(not_archived(ScreenApp.archived_at))
    return list(session.exec(statement).all())


def get_screen_app(session: Session, slug: str) -> ScreenApp:
    return require_screen_app(session, normalize_slug(slug))


def update_screen_app(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    category_slug: str | None = None,
) -> ScreenApp:
    app = require_screen_app(session, normalize_slug(slug))
    metric = metric_by_id(session, app.metric_id)
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        app.name = name
        metric.name = name
    if category_slug is not None:
        category = require_screen_category(session, normalize_slug(category_slug))
        if category.archived_at is not None:
            raise ValidationError(f"screen_category {category.slug!r} is archived")
        app.category_id = category.id
        metric.direction = direction_for_judgment(ScreenJudgment(category.judgment))
    session.add(metric)
    session.add(app)
    session.commit()
    session.refresh(app)
    return app


def create_screen_budget(
    session: Session,
    slug: str,
    *,
    target_kind: ScreenBudgetTargetKind,
    target_slug: str,
    period: Period,
    target_value: float,
    comparator: Comparator,
    name: str | None = None,
    active_from: date | None = None,
    active_to: date | None = None,
) -> ScreenBudget:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, ScreenBudget, slug)
    target_kind = ScreenBudgetTargetKind(target_kind)
    period = Period(period)
    comparator = Comparator(comparator)
    resolved_target = _validate_budget_target(session, target_kind, target_slug)
    if active_from is None:
        active_from = resolve_today(None)
    if active_to is not None and active_to < active_from:
        raise ValidationError("active_to must be on or after active_from")
    budget = ScreenBudget(
        slug=slug,
        name=name if name is not None else display_name(slug),
        target_kind=target_kind,
        target_slug=resolved_target,
        period=period,
        target_value=float(target_value),
        comparator=comparator,
        active_from=active_from,
        active_to=active_to,
    )
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def list_screen_budgets(session: Session) -> list[ScreenBudget]:
    return list(session.exec(select(ScreenBudget).order_by(ScreenBudget.slug)).all())


def get_screen_budget(session: Session, slug: str) -> ScreenBudget:
    return require_screen_budget(session, normalize_slug(slug))


def update_screen_budget(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    target_kind: ScreenBudgetTargetKind | None = None,
    target_slug: str | None = None,
    target_value: float | None = None,
    comparator: Comparator | None = None,
    active_to: date | None | object = _UNSET,
) -> ScreenBudget:
    budget = require_screen_budget(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        budget.name = name
    kind = (
        ScreenBudgetTargetKind(target_kind)
        if target_kind is not None
        else ScreenBudgetTargetKind(budget.target_kind)
    )
    raw_target = target_slug if target_slug is not None else budget.target_slug
    if target_kind is not None or target_slug is not None:
        budget.target_kind = kind
        budget.target_slug = _validate_budget_target(session, kind, raw_target)
    if target_value is not None:
        budget.target_value = float(target_value)
    if comparator is not None:
        budget.comparator = comparator
    if active_to is not _UNSET:
        if active_to is not None and (
            isinstance(active_to, datetime) or not isinstance(active_to, date)
        ):
            raise ValidationError("active_to must be a date or None")
        if isinstance(active_to, date) and active_to < budget.active_from:
            raise ValidationError("active_to must be on or after active_from")
        budget.active_to = active_to
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


def create_screen_device(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> ScreenDevice:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, ScreenDevice, slug)
    device = ScreenDevice(
        slug=slug,
        name=name if name is not None else display_name(slug),
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


def list_screen_devices(session: Session, *, include_archived: bool = False) -> list[ScreenDevice]:
    statement = select(ScreenDevice).order_by(ScreenDevice.slug)
    if not include_archived:
        statement = statement.where(not_archived(ScreenDevice.archived_at))
    return list(session.exec(statement).all())


def get_screen_device(session: Session, slug: str) -> ScreenDevice:
    return require_screen_device(session, normalize_slug(slug))


def update_screen_device(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> ScreenDevice:
    device = require_screen_device(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        device.name = name
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


def log_screen_session(
    session: Session,
    app_slug: str,
    *,
    minutes: float | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    occurred_on: date | None = None,
    device_slug: str | None = None,
    note: str | None = None,
    source: Source = Source.CLI,
) -> ScreenSession:
    app = require_screen_app(session, normalize_slug(app_slug))
    if app.archived_at is not None:
        raise ValidationError(f"screen_app {app.slug!r} is archived")
    device = _optional_device(session, device_slug)
    try:
        resolved = resolve_screen_session(
            started_at=started_at,
            ended_at=ended_at,
            minutes=minutes,
            occurred_on=occurred_on,
            timezone=load_settings().timezone,
            today=resolve_today(None),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    metric = metric_by_id(session, app.metric_id)
    entry = log_entry(
        session,
        metric.slug,
        resolved.minutes,
        occurred_on=resolved.occurred_on,
        occurred_at=resolved.started_at,
        note=note,
        source=source,
        link_screen=False,
    )
    row = ScreenSession(
        app_id=app.id,
        device_id=device.id if device is not None else None,
        started_at=resolved.started_at,
        ended_at=resolved.ended_at,
        minutes=resolved.minutes,
        occurred_on=resolved.occurred_on,
        note=note,
        source=source,
        entry_id=entry.id,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_screen_session(session: Session, session_id: int) -> ScreenSession:
    return require_screen_session(session, session_id)


def list_screen_sessions(
    session: Session,
    *,
    occurred_on: date | None = None,
) -> list[ScreenSession]:
    statement = select(ScreenSession).order_by(ScreenSession.id)
    if occurred_on is not None:
        statement = statement.where(ScreenSession.occurred_on == occurred_on)
    return list(session.exec(statement).all())


def update_screen_session(
    session: Session,
    session_id: int,
    *,
    minutes: float | None | object = _UNSET,
    started_at: datetime | None | object = _UNSET,
    ended_at: datetime | None | object = _UNSET,
    occurred_on: date | None | object = _UNSET,
    device_slug: str | None | object = _UNSET,
    note: str | None | object = _UNSET,
) -> ScreenSession:
    row = require_screen_session(session, session_id)
    next_start = row.started_at if started_at is _UNSET else started_at
    next_end = row.ended_at if ended_at is _UNSET else ended_at
    next_minutes = row.minutes if minutes is _UNSET else minutes
    next_occurred = row.occurred_on if occurred_on is _UNSET else occurred_on
    if started_at is not _UNSET and ended_at is not _UNSET and minutes is _UNSET:
        next_minutes = None
    if started_at is _UNSET and ended_at is _UNSET and minutes is not _UNSET:
        next_start = None
        next_end = None
    try:
        resolved = resolve_screen_session(
            started_at=next_start if isinstance(next_start, datetime) else None,
            ended_at=next_end if isinstance(next_end, datetime) else None,
            minutes=next_minutes if isinstance(next_minutes, int | float) else None,
            occurred_on=(
                next_occurred
                if isinstance(next_occurred, date) and not isinstance(next_occurred, datetime)
                else None
            ),
            timezone=load_settings().timezone,
            today=resolve_today(None),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if device_slug is not _UNSET:
        device = _optional_device(session, device_slug if isinstance(device_slug, str) else None)
        row.device_id = device.id if device is not None else None
    if note is not _UNSET:
        if note is not None and not isinstance(note, str):
            raise ValidationError("note must be a string or None")
        row.note = note
    row.started_at = resolved.started_at
    row.ended_at = resolved.ended_at
    row.minutes = resolved.minutes
    row.occurred_on = resolved.occurred_on
    session.add(row)
    if row.entry_id is not None:
        entry = require_entry(session, row.entry_id)
        entry.value_num = resolved.minutes
        entry.occurred_on = resolved.occurred_on
        entry.occurred_at = resolved.started_at
        entry.note = row.note
        session.add(entry)
    session.commit()
    session.refresh(row)
    return row


def delete_screen_session(session: Session, session_id: int) -> None:
    row = require_screen_session(session, session_id)
    entry_id = row.entry_id
    session.delete(row)
    session.flush()
    if entry_id is not None:
        entry = session.get(Entry, entry_id)
        if entry is not None:
            session.delete(entry)
    session.commit()


def _optional_device(session: Session, device_slug: str | None) -> ScreenDevice | None:
    if device_slug is None or device_slug == "":
        return None
    device = require_screen_device(session, normalize_slug(device_slug))
    if device.archived_at is not None:
        raise ValidationError(f"screen_device {device.slug!r} is archived")
    return device


def screen_view(session: Session, *, as_of: date | None = None) -> ScreenView:
    as_of = resolve_today(as_of)
    timezone = load_settings().timezone
    categories = list_screen_categories(session)
    apps = list_screen_apps(session)
    views = _session_views(session)
    by_app: dict[str, float | None] = {app.slug: None for app in apps}
    for view in views:
        minutes = attributed_day_minutes(view, timezone).get(as_of)
        if minutes:
            by_app[view.app_slug] = add_minutes(by_app.get(view.app_slug), minutes)
    by_category: dict[str, float | None] = {category.slug: None for category in categories}
    by_judgment: dict[ScreenJudgment, float | None] = {
        ScreenJudgment.USEFUL: None,
        ScreenJudgment.WASTE: None,
        ScreenJudgment.NEUTRAL: None,
    }
    category_by_id = {category.id: category for category in categories}
    app_by_slug = {app.slug: app for app in apps}
    for app in apps:
        category = category_by_id[app.category_id]
        minutes = by_app[app.slug]
        by_category[category.slug] = add_minutes(by_category[category.slug], minutes)
        by_judgment[ScreenJudgment(category.judgment)] = add_minutes(
            by_judgment[ScreenJudgment(category.judgment)],
            minutes,
        )
    metric_by_id_map = {app.metric_id: metric_by_id(session, app.metric_id) for app in apps}
    app_rows_by_category: dict[int, list[ScreenAppRow]] = {
        category.id: [] for category in categories
    }
    for app in apps:
        category = category_by_id[app.category_id]
        app_rows_by_category[category.id].append(
            ScreenAppRow(
                slug=app.slug,
                name=app.name,
                category=category.slug,
                metric=metric_by_id_map[app.metric_id].slug,
                minutes=by_app[app.slug],
                archived_at=app.archived_at,
            )
        )
    category_rows = [
        ScreenCategoryRow(
            slug=category.slug,
            name=category.name,
            judgment=ScreenJudgment(category.judgment),
            minutes=by_category[category.slug],
            apps=app_rows_by_category[category.id],
            archived_at=category.archived_at,
        )
        for category in categories
    ]
    specs = [_app_spec(session, app, category_by_id) for app in apps]
    category_specs = [
        ScreenCategorySpec(slug=category.slug, judgment=ScreenJudgment(category.judgment))
        for category in categories
    ]
    entries_by_metric = session_entry_views(views, timezone)
    return ScreenView(
        as_of=as_of,
        categories=category_rows,
        judgments=ScreenJudgmentTotals(
            useful=by_judgment[ScreenJudgment.USEFUL],
            waste=by_judgment[ScreenJudgment.WASTE],
            neutral=by_judgment[ScreenJudgment.NEUTRAL],
            total=minutes_in_range(views, as_of, as_of, timezone),
        ),
        sessions=_sessions_on(
            views, app_by_slug, category_by_id, metric_by_id_map, as_of, timezone
        ),
        budgets=[
            _budget_status(budget, specs, category_specs, entries_by_metric, as_of)
            for budget in list_screen_budgets(session)
        ],
    )


def screen_dashboard(
    session: Session,
    *,
    as_of: date | None = None,
    period: Period = Period.WEEK,
) -> ScreenDashboard:
    as_of = resolve_today(as_of)
    period = Period(period)
    timezone = load_settings().timezone
    views = _session_views(session)
    math = screen_dashboard_math(views, as_of=as_of, period=period, timezone=timezone)
    categories = list_screen_categories(session)
    apps = list_screen_apps(session)
    category_by_id = {category.id: category for category in categories}
    specs = [_app_spec(session, app, category_by_id) for app in apps]
    category_specs = [
        ScreenCategorySpec(slug=category.slug, judgment=ScreenJudgment(category.judgment))
        for category in categories
    ]
    entries_by_metric = session_entry_views(views, timezone)
    budgets = [
        _budget_status(budget, specs, category_specs, entries_by_metric, as_of)
        for budget in list_screen_budgets(session)
    ]
    insights = [*math.insights, *_budget_insights(budgets)]
    return ScreenDashboard(
        period=math.period,
        as_of=math.as_of,
        range_start=math.range_start,
        range_end=math.range_end,
        previous_start=math.previous_start,
        previous_end=math.previous_end,
        total=math.total,
        daily_average=math.daily_average,
        longest_day=math.longest_day,
        delta_minutes=math.delta_minutes,
        delta_fraction=math.delta_fraction,
        score=math.score,
        score_band=math.score_band,
        judgments=ScreenJudgmentTotals(
            useful=math.useful,
            waste=math.waste,
            neutral=math.neutral,
            total=math.total,
        ),
        apps=list(math.apps),
        categories=list(math.categories),
        devices=list(math.devices),
        daily=list(math.daily),
        comparison=list(math.comparison),
        hours=[list(row) for row in math.hours],
        trend=list(math.trend),
        insights=insights,
        budgets=budgets,
    )


def _ensure_screen_area(session: Session) -> Area:
    existing = session.exec(select(Area).where(Area.slug == SCREEN_AREA_SLUG)).first()
    if existing is not None:
        if existing.archived_at is not None:
            raise ValidationError(f"area {SCREEN_AREA_SLUG!r} is archived")
        return existing
    area = Area(slug=SCREEN_AREA_SLUG, name="Screen", description="Apps, categories, and budgets.")
    session.add(area)
    session.flush()
    return area


def _apps_for_category(session: Session, category_id: int | None) -> list[ScreenApp]:
    return list(
        session.exec(
            select(ScreenApp)
            .where(ScreenApp.category_id == category_id)
            .where(not_archived(ScreenApp.archived_at))
        ).all()
    )


def _validate_budget_target(
    session: Session,
    target_kind: ScreenBudgetTargetKind,
    target_slug: str,
) -> str:
    if target_kind is ScreenBudgetTargetKind.JUDGMENT:
        try:
            return str(ScreenJudgment(target_slug))
        except ValueError as exc:
            raise ValidationError(
                f"judgment target must be one of {[item.value for item in ScreenJudgment]}"
            ) from exc
    category = require_screen_category(session, normalize_slug(target_slug))
    if category.archived_at is not None:
        raise ValidationError(f"screen_category {category.slug!r} is archived")
    return category.slug


def _app_spec(
    session: Session,
    app: ScreenApp,
    category_by_id: dict[int | None, ScreenCategory],
) -> ScreenAppSpec:
    category = category_by_id[app.category_id]
    metric = metric_by_id(session, app.metric_id)
    return ScreenAppSpec(slug=app.slug, category_slug=category.slug, metric_slug=metric.slug)


def _session_views(session: Session) -> list[ScreenSessionView]:
    categories = {
        category.id: category for category in list_screen_categories(session, include_archived=True)
    }
    apps = {app.id: app for app in list_screen_apps(session, include_archived=True)}
    devices = {device.id: device for device in list_screen_devices(session, include_archived=True)}
    views: list[ScreenSessionView] = []
    for row in list_screen_sessions(session):
        app = apps.get(row.app_id)
        if app is None:
            continue
        category = categories[app.category_id]
        device = devices.get(row.device_id) if row.device_id is not None else None
        views.append(
            ScreenSessionView(
                id=row.id,
                minutes=row.minutes,
                occurred_on=row.occurred_on,
                started_at=_coerce_utc(row.started_at),
                ended_at=_coerce_utc(row.ended_at),
                app_slug=app.slug,
                app_name=app.name,
                category_slug=category.slug,
                category_name=category.name,
                judgment=ScreenJudgment(category.judgment),
                device_slug=device.slug if device is not None else None,
                device_name=device.name if device is not None else None,
                note=row.note,
            )
        )
    return views


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _sessions_on(
    views: list[ScreenSessionView],
    apps: dict[str, ScreenApp],
    category_by_id: dict[int | None, ScreenCategory],
    metric_by_id_map: dict[int | None, Metric],
    as_of: date,
    timezone,
) -> list[ScreenSessionRow]:
    sessions: list[ScreenSessionRow] = []
    for view in views:
        minutes = attributed_day_minutes(view, timezone).get(as_of)
        if not minutes or view.id is None:
            continue
        app = apps[view.app_slug]
        category = category_by_id[app.category_id]
        metric = metric_by_id_map[app.metric_id]
        sessions.append(
            ScreenSessionRow(
                id=view.id,
                app=view.app_slug,
                category=category.slug,
                metric=metric.slug,
                occurred_on=as_of,
                minutes=minutes,
                note=view.note,
            )
        )
    sessions.sort(key=lambda item: item.id)
    return sessions


def _budget_status(
    budget: ScreenBudget,
    apps: list[ScreenAppSpec],
    categories: list[ScreenCategorySpec],
    entries_by_metric: dict[str, list],
    as_of: date,
) -> ScreenBudgetStatus:
    spec = ScreenBudgetSpec(
        target_kind=ScreenBudgetTargetKind(budget.target_kind),
        target_slug=budget.target_slug,
        period=Period(budget.period),
        target_value=budget.target_value,
        comparator=Comparator(budget.comparator),
        active_from=budget.active_from,
        active_to=budget.active_to,
    )
    habit = spec.as_habit()
    members = member_apps(apps, categories, spec)
    views = [entry for app in members for entry in entries_by_metric.get(app.metric_slug, [])]
    bucket = bucket_for(as_of, habit.period)
    scheduled = is_scheduled(habit, bucket, as_of)
    in_bucket = [
        view for view in views if bucket.start <= view.occurred_on <= min(bucket.end, as_of)
    ]
    current_value = rollup(in_bucket, habit.aggregation)
    return ScreenBudgetStatus(
        slug=budget.slug,
        name=budget.name,
        target_kind=spec.target_kind,
        target_slug=spec.target_slug,
        period=habit.period,
        target_value=habit.target_value,
        comparator=habit.comparator,
        current_value=current_value,
        satisfied=is_satisfied(current_value, habit.comparator, habit.target_value),
        scheduled=scheduled,
        current_streak=current_streak(habit, views, as_of),
        longest_streak=longest_streak(habit, views, as_of),
        adherence=adherence(habit, views, habit.active_from, as_of),
        as_of=as_of,
    )


def screen_minutes_in_range(
    session: Session,
    start: date,
    end: date,
) -> float:
    timezone = load_settings().timezone
    return minutes_in_range(_session_views(session), start, end, timezone) or 0.0


def _budget_insights(budgets: list[ScreenBudgetStatus]) -> list[ScreenInsight]:
    waste_caps = [
        budget
        for budget in budgets
        if budget.target_kind is ScreenBudgetTargetKind.JUDGMENT
        and budget.target_slug == ScreenJudgment.WASTE
    ]
    if not waste_caps:
        return [
            ScreenInsight(
                kind=ScreenInsightKind.BUDGET,
                summary="No waste cap is set.",
                prescription="Add a waste cap so the dashboard can flag when the ceiling breaks.",
            )
        ]
    over = [budget for budget in waste_caps if budget.scheduled and not budget.satisfied]
    if not over:
        return []
    names = ", ".join(budget.name for budget in over)
    return [
        ScreenInsight(
            kind=ScreenInsightKind.BUDGET,
            summary=f"{names} is over its cap.",
            prescription=(
                "Lower tonight's waste minutes or raise the cap "
                "if it is no longer the right ceiling."
            ),
        )
    ]
