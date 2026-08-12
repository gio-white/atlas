from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlmodel import Session, select

from atlas.db.models import Goal, Milestone
from atlas.domain import Comparator, GoalKind, GoalStatus, Measure, PaceStatus, ValueType
from atlas.domain.goals import goal_progress as compute_progress
from atlas.domain.goals import pace_status as compute_pace
from atlas.services.clock import resolve_today
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    entries_for_metric,
    metric_by_id,
    milestones_for_goal,
    require_active_area,
    require_active_metric,
    require_goal,
)
from atlas.services.mapping import entry_view, goal_spec, milestone_view
from atlas.services.slugs import display_name, normalize_slug


@dataclass(frozen=True, slots=True)
class MilestoneInput:
    name: str
    due_on: date | None = None


@dataclass(frozen=True, slots=True)
class GoalProgressReport:
    slug: str
    name: str
    kind: GoalKind
    status: GoalStatus
    metric_slug: str | None
    current: float | None
    baseline: float | None
    fraction: float | None
    target_met: bool
    pace: PaceStatus
    target_value: float | None
    start_on: date
    due_on: date
    as_of: date


def create_goal(
    session: Session,
    slug: str,
    *,
    area_slug: str,
    kind: GoalKind,
    start_on: date,
    due_on: date,
    name: str | None = None,
    metric_slug: str | None = None,
    target_value: float | None = None,
    comparator: Comparator | None = None,
    baseline_value: float | None = None,
    measure: Measure | None = None,
    milestones: Sequence[MilestoneInput] | None = None,
) -> Goal:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Goal, slug)
    if due_on < start_on:
        raise ValidationError("due_on must be on or after start_on")
    area = require_active_area(session, normalize_slug(area_slug))
    metric_id = _metric_id_for_goal(session, kind, area.id, metric_slug)
    _validate_kind_fields(kind, metric_slug, target_value, comparator, measure)
    goal = Goal(
        area_id=area.id,
        slug=slug,
        name=name if name is not None else display_name(slug),
        kind=kind,
        metric_id=metric_id,
        target_value=target_value,
        comparator=comparator,
        baseline_value=baseline_value,
        measure=measure,
        start_on=start_on,
        due_on=due_on,
        status=GoalStatus.ACTIVE,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    _add_milestones(session, goal, milestones or ())
    return goal


def list_goals(
    session: Session,
    *,
    area_slug: str | None = None,
    status: GoalStatus | None = None,
) -> list[Goal]:
    statement = select(Goal).order_by(Goal.slug)
    if area_slug is not None:
        area = require_active_area(session, normalize_slug(area_slug))
        statement = statement.where(Goal.area_id == area.id)
    if status is not None:
        statement = statement.where(Goal.status == status)
    return list(session.exec(statement).all())


def get_goal(session: Session, slug: str) -> Goal:
    return require_goal(session, normalize_slug(slug))


def goal_progress(session: Session, slug: str, *, as_of: date | None = None) -> GoalProgressReport:
    as_of = resolve_today(as_of)
    goal = require_goal(session, normalize_slug(slug))
    report = _report_for(session, goal, as_of)
    if _stamp_achieved(goal, report.target_met):
        session.add(goal)
        session.commit()
        session.refresh(goal)
        report = _report_for(session, goal, as_of)
    return report


def toggle_milestone(
    session: Session,
    goal_slug: str,
    name: str,
    *,
    done: bool | None = None,
    as_of: date | None = None,
) -> Milestone:
    goal = require_goal(session, normalize_slug(goal_slug))
    milestone = _milestone_by_name(session, goal.id, name)
    now = datetime.now(UTC)
    should_complete = (milestone.done_at is None) if done is None else done
    milestone.done_at = now if should_complete else None
    session.add(milestone)
    report = _report_for(session, goal, resolve_today(as_of))
    _stamp_achieved(goal, report.target_met)
    session.add(goal)
    session.commit()
    session.refresh(milestone)
    return milestone


def _metric_id_for_goal(
    session: Session, kind: GoalKind, area_id: int, metric_slug: str | None
) -> int | None:
    if kind is GoalKind.MILESTONE:
        return None
    if metric_slug is None:
        raise ValidationError("metric_target goals require a metric")
    metric = require_active_metric(session, normalize_slug(metric_slug))
    if ValueType(metric.value_type) is ValueType.TEXT:
        raise ValidationError("metric_target goals cannot target a text metric")
    if metric.area_id != area_id:
        raise ValidationError(
            f"metric {metric.slug!r} does not belong to the goal's area"
        )
    return metric.id


def _validate_kind_fields(
    kind: GoalKind,
    metric_slug: str | None,
    target_value: float | None,
    comparator: Comparator | None,
    measure: Measure | None,
) -> None:
    if kind is GoalKind.METRIC_TARGET:
        missing = [
            name
            for name, value in (
                ("metric", metric_slug),
                ("target_value", target_value),
                ("comparator", comparator),
                ("measure", measure),
            )
            if value is None
        ]
        if missing:
            raise ValidationError(
                "metric_target goals require " + ", ".join(missing)
            )
        return
    extra = [
        name
        for name, value in (
            ("metric", metric_slug),
            ("target_value", target_value),
            ("comparator", comparator),
            ("measure", measure),
        )
        if value is not None
    ]
    if extra:
        raise ValidationError("milestone goals must not set " + ", ".join(extra))


def _add_milestones(
    session: Session, goal: Goal, milestones: Sequence[MilestoneInput]
) -> None:
    seen: set[str] = set()
    for item in milestones:
        name = item.name.strip()
        if not name:
            raise ValidationError("milestone name must not be empty")
        if name in seen:
            raise ValidationError(f"duplicate milestone name {name!r}")
        seen.add(name)
        session.add(Milestone(goal_id=goal.id, name=name, due_on=item.due_on))
    if milestones:
        session.commit()
        session.refresh(goal)


def _milestone_by_name(session: Session, goal_id: int, name: str) -> Milestone:
    for milestone in milestones_for_goal(session, goal_id):
        if milestone.name == name:
            return milestone
    raise NotFoundError("milestone", name)


def _report_for(session: Session, goal: Goal, as_of: date) -> GoalProgressReport:
    spec = goal_spec(goal)
    entries = []
    metric_slug = None
    if goal.metric_id is not None:
        metric = metric_by_id(session, goal.metric_id)
        metric_slug = metric.slug
        entries = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
    milestones = [milestone_view(row) for row in milestones_for_goal(session, goal.id)]
    progress = compute_progress(spec, entries, milestones, as_of)
    return GoalProgressReport(
        slug=goal.slug,
        name=goal.name,
        kind=GoalKind(goal.kind),
        status=GoalStatus(goal.status),
        metric_slug=metric_slug,
        current=progress.current,
        baseline=progress.baseline,
        fraction=progress.fraction,
        target_met=progress.target_met,
        pace=compute_pace(spec, progress, as_of),
        target_value=goal.target_value,
        start_on=goal.start_on,
        due_on=goal.due_on,
        as_of=as_of,
    )


def _stamp_achieved(goal: Goal, target_met: bool) -> bool:
    if not target_met or GoalStatus(goal.status) is not GoalStatus.ACTIVE:
        return False
    goal.status = GoalStatus.ACHIEVED
    goal.achieved_at = datetime.now(UTC)
    return True
