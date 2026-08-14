from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel import Session, select

from atlas.db.models import Area, Metric, ScreenApp, ScreenBudget, ScreenCategory
from atlas.domain import (
    Aggregation,
    Comparator,
    Period,
    ScreenAppSpec,
    ScreenBudgetSpec,
    ScreenBudgetTargetKind,
    ScreenCategorySpec,
    ScreenJudgment,
    ValueType,
    adherence,
    bucket_for,
    current_streak,
    direction_for_judgment,
    is_satisfied,
    is_scheduled,
    longest_streak,
    member_apps,
    rollup,
    screen_day_totals,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    entries_for_metric,
    metric_by_id,
    not_archived,
    require_screen_app,
    require_screen_budget,
    require_screen_category,
)
from atlas.services.mapping import entry_view
from atlas.services.slugs import display_name, normalize_slug

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
class ScreenSession:
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
    sessions: list[ScreenSession]
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


def screen_view(session: Session, *, as_of: date | None = None) -> ScreenView:
    as_of = resolve_today(as_of)
    categories = list_screen_categories(session)
    apps = list_screen_apps(session)
    category_by_id = {category.id: category for category in categories}
    specs = [_app_spec(session, app, category_by_id) for app in apps]
    category_specs = [
        ScreenCategorySpec(slug=category.slug, judgment=ScreenJudgment(category.judgment))
        for category in categories
    ]
    entries_by_metric = {
        spec.metric_slug: [
            entry_view(entry) for entry in entries_for_metric(session, app.metric_id)
        ]
        for spec, app in zip(specs, apps, strict=True)
    }
    by_app, by_category, by_judgment = screen_day_totals(
        specs,
        category_specs,
        entries_by_metric,
        as_of,
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
    return ScreenView(
        as_of=as_of,
        categories=category_rows,
        judgments=ScreenJudgmentTotals(
            useful=by_judgment[ScreenJudgment.USEFUL],
            waste=by_judgment[ScreenJudgment.WASTE],
            neutral=by_judgment[ScreenJudgment.NEUTRAL],
            total=rollup(
                [
                    entry
                    for entries in entries_by_metric.values()
                    for entry in entries
                    if entry.occurred_on == as_of
                ],
                Aggregation.SUM,
            ),
        ),
        sessions=_sessions_on(session, apps, category_by_id, metric_by_id_map, as_of),
        budgets=[
            _budget_status(budget, specs, category_specs, entries_by_metric, as_of)
            for budget in list_screen_budgets(session)
        ],
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


def _sessions_on(
    session: Session,
    apps: list[ScreenApp],
    category_by_id: dict[int | None, ScreenCategory],
    metric_by_id_map: dict[int | None, Metric],
    as_of: date,
) -> list[ScreenSession]:
    sessions: list[ScreenSession] = []
    for app in apps:
        metric = metric_by_id_map[app.metric_id]
        category = category_by_id[app.category_id]
        for entry in entries_for_metric(session, app.metric_id):
            if entry.occurred_on != as_of or entry.id is None:
                continue
            sessions.append(
                ScreenSession(
                    id=entry.id,
                    app=app.slug,
                    category=category.slug,
                    metric=metric.slug,
                    occurred_on=entry.occurred_on,
                    minutes=entry.value_num,
                    note=entry.note,
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
    views = [
        entry
        for app in members
        for entry in entries_by_metric.get(app.metric_slug, [])
    ]
    bucket = bucket_for(as_of, habit.period)
    scheduled = is_scheduled(habit, bucket, as_of)
    in_bucket = [
        view
        for view in views
        if bucket.start <= view.occurred_on <= min(bucket.end, as_of)
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
