from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlmodel import Session, col, select

from atlas.db.models import Goal, Milestone, Task
from atlas.domain import (
    Comparator,
    GoalHorizon,
    GoalKind,
    GoalStatus,
    Measure,
    PaceStatus,
    Period,
    TaskBucket,
    TaskPriority,
    ValueType,
    bucket_for,
    infer_horizon,
    is_column_on_track,
    parent_horizon_is_valid,
    required_parent_horizon,
)
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
from atlas.settings import load_settings

_UNSET = object()


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
    horizon: GoalHorizon
    parent: str | None
    description: str | None


@dataclass(frozen=True, slots=True)
class GoalBoardColumn:
    horizon: GoalHorizon
    on_track: int
    total: int
    fraction: float | None
    goals: list[GoalProgressReport]


@dataclass(frozen=True, slots=True)
class GoalBoardTask:
    id: int
    title: str
    bucket: TaskBucket
    due_on: date | None
    due_at: datetime | None
    priority: TaskPriority
    done_at: datetime | None
    created_at: datetime
    goal: str | None


@dataclass(frozen=True, slots=True)
class GoalBoardWeek:
    total: int
    done: int
    fraction: float | None
    tasks: list[GoalBoardTask]


@dataclass(frozen=True, slots=True)
class GoalsBoard:
    as_of: date
    long: GoalBoardColumn
    medium: GoalBoardColumn
    short: GoalBoardColumn
    week: GoalBoardWeek


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
    horizon: GoalHorizon | None = None,
    parent_slug: str | None = None,
    description: str | None = None,
) -> Goal:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Goal, slug)
    if due_on < start_on:
        raise ValidationError("due_on must be on or after start_on")
    area = require_active_area(session, normalize_slug(area_slug))
    metric_id = _metric_id_for_goal(session, kind, area.id, metric_slug)
    _validate_kind_fields(kind, metric_slug, target_value, comparator, measure)
    resolved_horizon = horizon if horizon is not None else infer_horizon(start_on, due_on)
    parent_id = _parent_id_for(session, resolved_horizon, parent_slug)
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
        horizon=resolved_horizon,
        parent_id=parent_id,
        description=_clean_description(description),
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
    horizon: GoalHorizon | None = None,
    parent_slug: str | None = None,
) -> list[Goal]:
    statement = select(Goal).order_by(Goal.slug)
    if area_slug is not None:
        area = require_active_area(session, normalize_slug(area_slug))
        statement = statement.where(Goal.area_id == area.id)
    if status is not None:
        statement = statement.where(Goal.status == status)
    if horizon is not None:
        statement = statement.where(Goal.horizon == horizon)
    if parent_slug is not None:
        parent = require_goal(session, normalize_slug(parent_slug))
        statement = statement.where(Goal.parent_id == parent.id)
    return list(session.exec(statement).all())


@dataclass(frozen=True, slots=True)
class GoalDetail:
    goal: Goal
    milestones: list[Milestone]


def get_goal(session: Session, slug: str) -> Goal:
    return require_goal(session, normalize_slug(slug))


def get_goal_detail(session: Session, slug: str) -> GoalDetail:
    goal = get_goal(session, slug)
    return GoalDetail(goal=goal, milestones=milestones_for_goal(session, goal.id))


def update_goal(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    due_on: date | None = None,
    target_value: float | None = None,
    status: GoalStatus | None = None,
    horizon: GoalHorizon | None = None,
    parent_slug: str | None | object = _UNSET,
    description: str | None | object = _UNSET,
) -> Goal:
    goal = require_goal(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        goal.name = name
    if due_on is not None:
        if due_on < goal.start_on:
            raise ValidationError("due_on must be on or after start_on")
        goal.due_on = due_on
    if target_value is not None:
        if GoalKind(goal.kind) is GoalKind.MILESTONE:
            raise ValidationError("milestone goals cannot set target_value")
        goal.target_value = target_value
    if status is not None:
        if status is GoalStatus.ACHIEVED:
            raise ValidationError(
                "status cannot be set to achieved; it is stamped when the target is met"
            )
        goal.status = status
        goal.achieved_at = None
    new_horizon = horizon if horizon is not None else GoalHorizon(goal.horizon)
    if horizon is not None and horizon is not GoalHorizon(goal.horizon):
        if _children_of(session, goal.id):
            raise ValidationError("cannot change horizon while the goal has children")
        goal.horizon = horizon
    if parent_slug is not _UNSET:
        goal.parent_id = _parent_id_for(
            session, new_horizon, parent_slug, child_id=goal.id
        )
    elif not parent_horizon_is_valid(
        new_horizon,
        _horizon_of(session.get(Goal, goal.parent_id)) if goal.parent_id is not None else None,
    ):
        raise ValidationError(_parent_mismatch_message(new_horizon))
    if description is not _UNSET:
        goal.description = _clean_description(description if isinstance(description, str) else None)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


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


def goals_board(session: Session, *, as_of: date | None = None) -> GoalsBoard:
    as_of = resolve_today(as_of)
    goals = list(session.exec(select(Goal).order_by(Goal.slug)).all())
    slug_by_id = {goal.id: goal.slug for goal in goals if goal.id is not None}
    grouped: dict[GoalHorizon, list[GoalProgressReport]] = {
        GoalHorizon.LONG: [],
        GoalHorizon.MEDIUM: [],
        GoalHorizon.SHORT: [],
    }
    for goal in goals:
        if GoalStatus(goal.status) in {GoalStatus.PAUSED, GoalStatus.ABANDONED}:
            continue
        grouped[GoalHorizon(goal.horizon)].append(_report_for(session, goal, as_of, slug_by_id))
    return GoalsBoard(
        as_of=as_of,
        long=_column_for(GoalHorizon.LONG, grouped[GoalHorizon.LONG]),
        medium=_column_for(GoalHorizon.MEDIUM, grouped[GoalHorizon.MEDIUM]),
        short=_column_for(GoalHorizon.SHORT, grouped[GoalHorizon.SHORT]),
        week=_week_column(session, as_of, slug_by_id),
    )


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


def _parent_id_for(
    session: Session,
    horizon: GoalHorizon,
    parent_slug: str | None,
    *,
    child_id: int | None = None,
) -> int | None:
    if parent_slug is None:
        if not parent_horizon_is_valid(horizon, None):
            raise ValidationError(_parent_mismatch_message(horizon))
        return None
    parent = require_goal(session, normalize_slug(parent_slug))
    if child_id is not None and parent.id == child_id:
        raise ValidationError("a goal cannot be its own parent")
    parent_horizon = GoalHorizon(parent.horizon)
    if not parent_horizon_is_valid(horizon, parent_horizon):
        raise ValidationError(_parent_mismatch_message(horizon))
    return parent.id


def _parent_mismatch_message(horizon: GoalHorizon) -> str:
    required = required_parent_horizon(horizon)
    if required is None:
        return "long-term goals cannot have a parent"
    return f"{horizon} goals may only parent under a {required} goal"


def _children_of(session: Session, goal_id: int | None) -> list[Goal]:
    if goal_id is None:
        return []
    statement = select(Goal).where(Goal.parent_id == goal_id)
    return list(session.exec(statement).all())


def _horizon_of(goal: Goal | None) -> GoalHorizon | None:
    if goal is None:
        return None
    return GoalHorizon(goal.horizon)


def _clean_description(description: str | None) -> str | None:
    if description is None:
        return None
    cleaned = description.strip()
    return cleaned or None


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


def _report_for(
    session: Session,
    goal: Goal,
    as_of: date,
    slug_by_id: dict[int | None, str] | None = None,
) -> GoalProgressReport:
    spec = goal_spec(goal)
    entries = []
    metric_slug = None
    if goal.metric_id is not None:
        metric = metric_by_id(session, goal.metric_id)
        metric_slug = metric.slug
        entries = [entry_view(entry) for entry in entries_for_metric(session, metric.id)]
    milestones = [milestone_view(row) for row in milestones_for_goal(session, goal.id)]
    progress = compute_progress(spec, entries, milestones, as_of)
    parent = None
    if goal.parent_id is not None:
        if slug_by_id is not None:
            parent = slug_by_id.get(goal.parent_id)
        else:
            row = session.get(Goal, goal.parent_id)
            parent = row.slug if row is not None else None
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
        horizon=GoalHorizon(goal.horizon),
        parent=parent,
        description=goal.description,
    )


def _column_for(horizon: GoalHorizon, reports: list[GoalProgressReport]) -> GoalBoardColumn:
    total = len(reports)
    on_track = sum(1 for report in reports if is_column_on_track(report.pace))
    fraction = None if total == 0 else on_track / total
    return GoalBoardColumn(
        horizon=horizon,
        on_track=on_track,
        total=total,
        fraction=fraction,
        goals=reports,
    )


def _week_column(
    session: Session,
    as_of: date,
    slug_by_id: dict[int | None, str],
) -> GoalBoardWeek:
    week = bucket_for(as_of, Period.WEEK)
    timezone = load_settings().timezone
    selected: list[GoalBoardTask] = []
    statement = select(Task).where(col(Task.goal_id).is_not(None)).order_by(Task.id)
    for task in session.exec(statement).all():
        if not _task_on_week_board(task, week.start, week.end, timezone):
            continue
        selected.append(
            GoalBoardTask(
                id=task.id or 0,
                title=task.title,
                bucket=TaskBucket(task.bucket),
                due_on=task.due_on,
                due_at=task.due_at,
                priority=TaskPriority(task.priority),
                done_at=task.done_at,
                created_at=task.created_at,
                goal=slug_by_id.get(task.goal_id),
            )
        )
    total = len(selected)
    done = sum(1 for task in selected if task.done_at is not None)
    fraction = None if total == 0 else done / total
    return GoalBoardWeek(total=total, done=done, fraction=fraction, tasks=selected)


def _task_on_week_board(
    task: Task, week_start: date, week_end: date, timezone
) -> bool:
    if task.due_on is not None and week_start <= task.due_on <= week_end:
        return True
    if task.done_at is not None:
        done_at = task.done_at
        if done_at.tzinfo is None:
            done_at = done_at.replace(tzinfo=UTC)
        done_on = done_at.astimezone(timezone).date()
        if week_start <= done_on <= week_end:
            return True
    return (
        task.due_on is None
        and task.done_at is None
        and TaskBucket(task.bucket) is TaskBucket.TODAY
    )


def _stamp_achieved(goal: Goal, target_met: bool) -> bool:
    if not target_met or GoalStatus(goal.status) is not GoalStatus.ACTIVE:
        return False
    goal.status = GoalStatus.ACHIEVED
    goal.achieved_at = datetime.now(UTC)
    return True
