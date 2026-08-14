from datetime import date

from atlas.domain import TaskBucket, TaskPriority
from atlas.services import create_task, list_tasks, tasks_done_in_week, update_task


def test_create_list_and_complete_task(session):
    task = create_task(
        session,
        "Family time",
        bucket=TaskBucket.TODAY,
        due_on=date(2026, 8, 14),
        priority=TaskPriority.HIGH,
    )
    assert task.id is not None
    assert [row.title for row in list_tasks(session)] == ["Family time"]
    done = update_task(session, task.id, done=True)
    assert done.done_at is not None
    assert list_tasks(session) == []
    assert list_tasks(session, include_done=True)[0].title == "Family time"


def test_tasks_done_in_week_counts_completions(session):
    task = create_task(session, "Ship it", bucket=TaskBucket.TODAY)
    update_task(session, task.id, done=True)
    assert tasks_done_in_week(session) == 1
