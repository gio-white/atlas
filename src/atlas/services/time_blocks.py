"""Time block use cases: schedule, move, resize, delete, and record a session's outcome.

Completing a block never completes its task (plan §4.7); see docs/domain/time-blocks.md.
"""

from datetime import UTC, datetime

from sqlmodel import Session, col, select

from atlas.db.models import Task, TimeBlock
from atlas.domain import TaskStatus, TimeBlockStatus
from atlas.domain.quests import (
    QuestRuleError,
    as_utc,
    check_block_window,
    check_can_schedule,
    complete_block,
    overlapping_ids,
)
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.quests import (
    BlockItem,
    apply_task_times,
    block_item,
    block_view,
    task_times,
)


def list_time_blocks(
    session: Session,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    task_id: int | None = None,
    now: datetime | None = None,
) -> list[BlockItem]:
    """Blocks overlapping [start, end) (either bound optional), oldest first."""
    now = _now(now)
    statement = select(TimeBlock)
    if start is not None:
        statement = statement.where(col(TimeBlock.end_at) > _db(start))
    if end is not None:
        statement = statement.where(col(TimeBlock.start_at) < _db(end))
    if task_id is not None:
        statement = statement.where(TimeBlock.task_id == task_id)
    rows = list(session.exec(statement.order_by(col(TimeBlock.start_at), col(TimeBlock.id))).all())
    overlaps = overlapping_ids([block_view(row) for row in rows])
    return [block_item(row, now, overlaps=row.id in overlaps) for row in rows]


def get_time_block(session: Session, block_id: int, *, now: datetime | None = None) -> BlockItem:
    return block_item(_require(session, block_id), _now(now))


def create_time_block(
    session: Session,
    *,
    task_id: int,
    start_at: datetime,
    end_at: datetime,
    now: datetime | None = None,
) -> BlockItem:
    now = _now(now)
    task = session.get(Task, task_id)
    if task is None:
        raise ValidationError(f"task {task_id} does not exist")
    _rule(
        lambda: check_can_schedule(
            TaskStatus(task.status), task_archived=task.archived_at is not None
        )
    )
    _rule(lambda: check_block_window(start_at, end_at))
    row = TimeBlock(
        task_id=task_id,
        start_at=_db(start_at),
        end_at=_db(end_at),
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return block_item(row, now)


def update_time_block(
    session: Session,
    block_id: int,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    now: datetime | None = None,
) -> BlockItem:
    """Move or resize a block."""
    now = _now(now)
    row = _require(session, block_id)
    new_start = as_utc(start_at) if start_at is not None else as_utc(row.start_at)
    new_end = as_utc(end_at) if end_at is not None else as_utc(row.end_at)
    _rule(lambda: check_block_window(new_start, new_end))
    row.start_at = _db(new_start)
    row.end_at = _db(new_end)
    row.updated_at = now
    session.add(row)
    session.commit()
    return block_item(row, now)


def delete_time_block(session: Session, block_id: int) -> None:
    session.delete(_require(session, block_id))
    session.commit()


def complete_time_block(
    session: Session, block_id: int, *, now: datetime | None = None
) -> BlockItem:
    """Session done: the block is completed and a `todo` task moves to `in_progress`."""
    now = _now(now)
    row = _require(session, block_id)
    task = session.get(Task, row.task_id)
    assert task is not None
    outcome = complete_block(task_times(task), now)
    row.status = outcome.block_status
    row.updated_at = now
    if outcome.task != task_times(task):
        apply_task_times(task, outcome.task)
        task.updated_at = now
        session.add(task)
    session.add(row)
    session.commit()
    return block_item(row, now)


def cancel_time_block(session: Session, block_id: int, *, now: datetime | None = None) -> BlockItem:
    """The session did not happen. The row is kept and the task is unchanged."""
    now = _now(now)
    row = _require(session, block_id)
    row.status = TimeBlockStatus.CANCELLED
    row.updated_at = now
    session.add(row)
    session.commit()
    return block_item(row, now)


def _require(session: Session, block_id: int) -> TimeBlock:
    row = session.get(TimeBlock, block_id)
    if row is None:
        raise NotFoundError("time_block", block_id)
    return row


def _rule(check) -> None:
    try:
        check()
    except QuestRuleError as exc:
        raise ValidationError(str(exc)) from exc


def _db(value: datetime) -> datetime:
    """UTC without tzinfo: SQLite stores datetimes as naive text, so bind them the same way."""
    return as_utc(value).replace(tzinfo=None)


def _now(now: datetime | None) -> datetime:
    return as_utc(now) if now is not None else datetime.now(UTC)
