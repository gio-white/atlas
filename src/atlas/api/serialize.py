from typing import Any

from sqlmodel import Session

from atlas.api.schemas import (
    EntryOut,
    HabitBreakOut,
    HabitCheckInOut,
    HabitDetailOut,
    HabitOut,
    HabitStatusOut,
    LibraryTitleOut,
    LibraryTopicOut,
    LibraryTopicRefOut,
    MetricOut,
    ScreenAppOut,
    ScreenBudgetOut,
    ScreenCategoryOut,
    ScreenDeviceOut,
    ScreenSessionRecordOut,
    SleepSessionOut,
    SleepStageOut,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    HabitKind,
    MetricOrigin,
    Period,
    ScreenBudgetTargetKind,
    ScreenJudgment,
    Source,
    TimeOfDay,
    ValueType,
)
from atlas.services import (
    list_metrics,
    list_screen_apps,
    list_screen_categories,
    list_screen_devices,
    sleep_stages,
    title_view_for,
)


def metric_slug_by_id(session: Session) -> dict[int, str]:
    return {
        metric.id: metric.slug
        for metric in list_metrics(session, include_archived=True)
        if metric.id is not None
    }


def metric_out(metric: Any) -> MetricOut:
    return MetricOut(
        id=metric.id,
        slug=metric.slug,
        origin=MetricOrigin(metric.origin),
        name=metric.name,
        value_type=ValueType(metric.value_type),
        unit=metric.unit,
        aggregation=Aggregation(metric.aggregation),
        direction=Direction(metric.direction),
        archived_at=metric.archived_at,
    )


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


def habit_out(habit: Any, metric: Any) -> HabitOut:
    return HabitOut(
        id=habit.id,
        slug=habit.slug,
        metric=metric.slug,
        name=habit.name,
        kind=HabitKind(habit.kind),
        period=Period(habit.period),
        target_value=habit.target_value,
        comparator=Comparator(habit.comparator),
        unit=metric.unit,
        weekdays=list(habit.weekdays) if habit.weekdays is not None else None,
        time_of_day=TimeOfDay(habit.time_of_day),
        active_from=habit.active_from,
        active_to=habit.active_to,
        archived_at=habit.archived_at,
    )


def habits_out(session: Session, habits: list[Any]) -> list[HabitOut]:
    metrics = {metric.id: metric for metric in list_metrics(session, include_archived=True)}
    return [habit_out(habit, metrics[habit.metric_id]) for habit in habits]


def habit_detail_out(session: Session, detail: Any) -> HabitDetailOut:
    return HabitDetailOut(
        habit=habits_out(session, [detail.habit])[0],
        status=HabitStatusOut.model_validate(detail.status),
        breaks=[HabitBreakOut.model_validate(row) for row in detail.breaks],
        recent=[HabitCheckInOut.model_validate(row) for row in detail.recent],
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


def sleep_session_out(session: Session, row: Any) -> SleepSessionOut:
    return SleepSessionOut(
        id=row.id,
        started_at=row.started_at,
        ended_at=row.ended_at,
        occurred_on=row.occurred_on,
        note=row.note,
        source=Source(row.source),
        created_at=row.created_at,
        stages=[SleepStageOut.model_validate(stage) for stage in sleep_stages(session, row.id)],
    )


def library_topic_out(topic: Any) -> LibraryTopicOut:
    return LibraryTopicOut(
        id=topic.id,
        slug=topic.slug,
        name=topic.name,
        archived_at=topic.archived_at,
    )


def library_title_out(view: Any) -> LibraryTitleOut:
    return LibraryTitleOut(
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
        rating=view.rating,
        link=view.link,
        topics=[LibraryTopicRefOut(slug=topic.slug, name=topic.name) for topic in view.topics],
        image=view.image,
        created_at=view.created_at,
    )


def library_title_out_for(session: Session, title: Any) -> LibraryTitleOut:
    return library_title_out(title_view_for(session, title))
