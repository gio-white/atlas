from typing import Any

from sqlmodel import Session

from atlas.api.schemas import (
    EntertainmentTitleOut,
    EntertainmentTopicOut,
    EntertainmentTopicRefOut,
    EntryOut,
    GoalDetailOut,
    GoalOut,
    HabitOut,
    MetricOut,
    MilestoneOut,
    ScreenAppOut,
    ScreenBudgetOut,
    ScreenCategoryOut,
    ScreenDeviceOut,
    ScreenSessionRecordOut,
    TaskOut,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
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
)
from atlas.services import (
    list_areas,
    list_goals,
    list_metrics,
    list_screen_apps,
    list_screen_categories,
    list_screen_devices,
    title_view_for,
)


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


def goal_out(
    goal: Any,
    area_slug: str | None,
    metric_slug: str | None,
    parent_slug: str | None,
) -> GoalOut:
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
        horizon=GoalHorizon(goal.horizon),
        parent=parent_slug,
        description=goal.description,
        status=GoalStatus(goal.status),
        achieved_at=goal.achieved_at,
    )


def goal_slug_by_id(session: Session) -> dict[int, str]:
    return {goal.id: goal.slug for goal in list_goals(session) if goal.id is not None}


def goals_out(session: Session, goals: list[Any]) -> list[GoalOut]:
    areas = area_slug_by_id(session)
    metrics = metric_slug_by_id(session)
    parents = goal_slug_by_id(session)
    return [
        goal_out(
            goal,
            areas.get(goal.area_id) if goal.area_id is not None else None,
            metrics.get(goal.metric_id) if goal.metric_id is not None else None,
            parents.get(goal.parent_id) if goal.parent_id is not None else None,
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
        areas.get(detail.goal.area_id) if detail.goal.area_id is not None else None,
        metrics.get(detail.goal.metric_id) if detail.goal.metric_id is not None else None,
        goal_slug_by_id(session).get(detail.goal.parent_id)
        if detail.goal.parent_id is not None
        else None,
    )
    return GoalDetailOut(
        **base.model_dump(),
        milestones=[milestone_out(item) for item in detail.milestones],
    )


def screen_category_out(category: Any) -> ScreenCategoryOut:
    return ScreenCategoryOut(
        id=category.id,
        slug=category.slug,
        name=category.name,
        judgment=ScreenJudgment(category.judgment),
        archived_at=category.archived_at,
    )


def screen_app_out(app: Any, category_slug: str, metric_slug: str) -> ScreenAppOut:
    return ScreenAppOut(
        id=app.id,
        slug=app.slug,
        name=app.name,
        category=category_slug,
        metric=metric_slug,
        archived_at=app.archived_at,
    )


def screen_apps_out(session: Session, apps: list[Any]) -> list[ScreenAppOut]:
    categories = {
        category.id: category.slug
        for category in list_screen_categories(session, include_archived=True)
        if category.id is not None
    }
    metrics = metric_slug_by_id(session)
    return [
        screen_app_out(app, categories[app.category_id], metrics[app.metric_id]) for app in apps
    ]


def task_out(task: Any, goal_slug: str | None) -> TaskOut:
    return TaskOut(
        id=task.id,
        title=task.title,
        bucket=TaskBucket(task.bucket),
        due_on=task.due_on,
        due_at=task.due_at,
        priority=TaskPriority(task.priority),
        goal=goal_slug,
        done_at=task.done_at,
        created_at=task.created_at,
    )


def tasks_out(session: Session, tasks: list[Any]) -> list[TaskOut]:
    goals = goal_slug_by_id(session)
    return [
        task_out(task, goals.get(task.goal_id) if task.goal_id is not None else None)
        for task in tasks
    ]


def screen_budget_out(budget: Any) -> ScreenBudgetOut:
    return ScreenBudgetOut(
        id=budget.id,
        slug=budget.slug,
        name=budget.name,
        target_kind=ScreenBudgetTargetKind(budget.target_kind),
        target_slug=budget.target_slug,
        period=Period(budget.period),
        target_value=budget.target_value,
        comparator=Comparator(budget.comparator),
        active_from=budget.active_from,
        active_to=budget.active_to,
    )


def screen_device_out(device: Any) -> ScreenDeviceOut:
    return ScreenDeviceOut(
        id=device.id,
        slug=device.slug,
        name=device.name,
        archived_at=device.archived_at,
    )


def screen_session_record_out(
    row: Any,
    app_slug: str,
    device_slug: str | None,
) -> ScreenSessionRecordOut:
    return ScreenSessionRecordOut(
        id=row.id,
        app=app_slug,
        device=device_slug,
        started_at=row.started_at,
        ended_at=row.ended_at,
        minutes=row.minutes,
        occurred_on=row.occurred_on,
        note=row.note,
        source=Source(row.source),
        created_at=row.created_at,
        entry_id=row.entry_id,
    )


def screen_session_records_out(session: Session, rows: list[Any]) -> list[ScreenSessionRecordOut]:
    apps = {
        app.id: app.slug
        for app in list_screen_apps(session, include_archived=True)
        if app.id is not None
    }
    devices = {
        device.id: device.slug
        for device in list_screen_devices(session, include_archived=True)
        if device.id is not None
    }
    return [
        screen_session_record_out(
            row,
            apps[row.app_id],
            devices.get(row.device_id) if row.device_id is not None else None,
        )
        for row in rows
    ]


def entertainment_topic_out(topic: Any) -> EntertainmentTopicOut:
    return EntertainmentTopicOut(
        id=topic.id,
        slug=topic.slug,
        name=topic.name,
        archived_at=topic.archived_at,
    )


def entertainment_title_out(view: Any) -> EntertainmentTitleOut:
    return EntertainmentTitleOut(
        slug=view.slug,
        name=view.name,
        kind=view.kind,
        creator=view.creator,
        recommended_by=view.recommended_by,
        status=view.status,
        started_on=view.started_on,
        finished_on=view.finished_on,
        progress=view.progress,
        note=view.note,
        topics=[
            EntertainmentTopicRefOut(slug=topic.slug, name=topic.name) for topic in view.topics
        ],
        image=view.image,
    )


def entertainment_title_out_for(session: Session, title: Any) -> EntertainmentTitleOut:
    return entertainment_title_out(title_view_for(session, title))
