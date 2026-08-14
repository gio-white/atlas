from typing import Any

from sqlmodel import Session

from atlas.api.schemas import EntryOut, GoalDetailOut, GoalOut, HabitOut, MetricOut, MilestoneOut
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    Source,
    ValueType,
)
from atlas.services import list_areas, list_metrics


def area_slug_by_id(session: Session) -> dict[int, str]:
    return {
        area.id: area.slug
        for area in list_areas(session, include_archived=True)
        if area.id is not None
    }


def metric_slug_by_id(session: Session) -> dict[int, str]:
    return {
        metric.id: metric.slug
        for metric in list_metrics(session, include_archived=True)
        if metric.id is not None
    }


def metric_out(metric: Any, area_slug: str) -> MetricOut:
    return MetricOut(
        id=metric.id,
        slug=metric.slug,
        area=area_slug,
        name=metric.name,
        value_type=ValueType(metric.value_type),
        unit=metric.unit,
        aggregation=Aggregation(metric.aggregation),
        direction=Direction(metric.direction),
        archived_at=metric.archived_at,
    )


def metrics_out(session: Session, metrics: list[Any]) -> list[MetricOut]:
    areas = area_slug_by_id(session)
    return [metric_out(metric, areas[metric.area_id]) for metric in metrics]


def entry_out(entry: Any, metric_slug: str) -> EntryOut:
    return EntryOut(
        id=entry.id,
        metric=metric_slug,
        occurred_on=entry.occurred_on,
        occurred_at=entry.occurred_at,
        value_num=entry.value_num,
        value_bool=entry.value_bool,
        value_text=entry.value_text,
        note=entry.note,
        source=Source(entry.source),
        created_at=entry.created_at,
    )


def entry_out_for(session: Session, entry: Any) -> EntryOut:
    return entry_out(entry, metric_slug_by_id(session)[entry.metric_id])


def habit_out(habit: Any, metric_slug: str) -> HabitOut:
    return HabitOut(
        id=habit.id,
        slug=habit.slug,
        metric=metric_slug,
        name=habit.name,
        period=Period(habit.period),
        target_value=habit.target_value,
        comparator=Comparator(habit.comparator),
        weekdays=list(habit.weekdays) if habit.weekdays is not None else None,
        active_from=habit.active_from,
        active_to=habit.active_to,
    )


def habits_out(session: Session, habits: list[Any]) -> list[HabitOut]:
    metrics = metric_slug_by_id(session)
    return [habit_out(habit, metrics[habit.metric_id]) for habit in habits]


def goal_out(goal: Any, area_slug: str, metric_slug: str | None) -> GoalOut:
    return GoalOut(
        id=goal.id,
        slug=goal.slug,
        area=area_slug,
        name=goal.name,
        kind=GoalKind(goal.kind),
        metric=metric_slug,
        target_value=goal.target_value,
        comparator=Comparator(goal.comparator) if goal.comparator is not None else None,
        baseline_value=goal.baseline_value,
        measure=Measure(goal.measure) if goal.measure is not None else None,
        start_on=goal.start_on,
        due_on=goal.due_on,
        status=GoalStatus(goal.status),
        achieved_at=goal.achieved_at,
    )


def goals_out(session: Session, goals: list[Any]) -> list[GoalOut]:
    areas = area_slug_by_id(session)
    metrics = metric_slug_by_id(session)
    return [
        goal_out(
            goal,
            areas[goal.area_id],
            metrics.get(goal.metric_id) if goal.metric_id is not None else None,
        )
        for goal in goals
    ]


def milestone_out(milestone: Any) -> MilestoneOut:
    return MilestoneOut(name=milestone.name, due_on=milestone.due_on, done_at=milestone.done_at)


def goal_detail_out(session: Session, detail: Any) -> GoalDetailOut:
    areas = area_slug_by_id(session)
    metrics = metric_slug_by_id(session)
    base = goal_out(
        detail.goal,
        areas[detail.goal.area_id],
        metrics.get(detail.goal.metric_id) if detail.goal.metric_id is not None else None,
    )
    return GoalDetailOut(
        **base.model_dump(),
        milestones=[milestone_out(item) for item in detail.milestones],
    )
