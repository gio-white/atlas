from datetime import UTC, date, datetime

from sqlmodel import Session, col, select

from atlas.db.models import Task
from atlas.domain import Period, TaskBucket, TaskPriority, bucket_for
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import require_goal, require_task
from atlas.services.slugs import normalize_slug

_UNSET = object()


def create_task(
    session: Session,
    title: str,
    *,
    bucket: TaskBucket = TaskBucket.TODAY,
    due_on: date | None = None,
    due_at: datetime | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    goal_slug: str | None = None,
) -> Task:
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("title must be a non-empty string")
    task = Task(
        title=cleaned,
        bucket=bucket,
        due_on=due_on,
        due_at=due_at,
        priority=priority,
        goal_id=_goal_id_for(session, goal_slug),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_tasks(
    session: Session,
    *,
    bucket: TaskBucket | None = None,
    include_done: bool = False,
    goal_slug: str | None = None,
) -> list[Task]:
    statement = select(Task).order_by(Task.id)
    if bucket is not None:
        statement = statement.where(Task.bucket == bucket)
    if not include_done:
        statement = statement.where(col(Task.done_at).is_(None))
    if goal_slug is not None:
        goal = require_goal(session, normalize_slug(goal_slug))
        statement = statement.where(Task.goal_id == goal.id)
    return list(session.exec(statement).all())


def get_task(session: Session, task_id: int) -> Task:
    return require_task(session, task_id)


def update_task(
    session: Session,
    task_id: int,
    *,
    title: str | None = None,
    bucket: TaskBucket | None = None,
    due_on: date | None | object = _UNSET,
    due_at: datetime | None | object = _UNSET,
    priority: TaskPriority | None = None,
    done: bool | None = None,
    goal_slug: str | None | object = _UNSET,
) -> Task:
    task = require_task(session, task_id)
    if title is not None:
        cleaned = title.strip()
        if not cleaned:
            raise ValidationError("title must be a non-empty string")
        task.title = cleaned
    if bucket is not None:
        task.bucket = bucket
    if due_on is not _UNSET:
        if due_on is not None and (
            isinstance(due_on, datetime) or not isinstance(due_on, date)
        ):
            raise ValidationError("due_on must be a date or None")
        task.due_on = due_on
    if due_at is not _UNSET:
        if due_at is not None and not isinstance(due_at, datetime):
            raise ValidationError("due_at must be a datetime or None")
        task.due_at = due_at
    if priority is not None:
        task.priority = priority
    if done is True:
        task.done_at = datetime.now(UTC)
    elif done is False:
        task.done_at = None
    if goal_slug is not _UNSET:
        task.goal_id = _goal_id_for(
            session, goal_slug if isinstance(goal_slug, str) else None
        )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def tasks_done_in_week(session: Session, *, as_of: date | None = None) -> int:
    as_of = resolve_today(as_of)
    week = bucket_for(as_of, Period.WEEK)
    count = 0
    for task in session.exec(select(Task).where(col(Task.done_at).is_not(None))).all():
        done_at = task.done_at
        if done_at.tzinfo is None:
            done_at = done_at.replace(tzinfo=UTC)
        done_on = done_at.astimezone(UTC).date()
        if week.start <= done_on <= min(week.end, as_of):
            count += 1
    return count


def _goal_id_for(session: Session, goal_slug: str | None) -> int | None:
    if goal_slug is None:
        return None
    return require_goal(session, normalize_slug(goal_slug)).id
