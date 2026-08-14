from datetime import date

from atlas.domain import GoalKind, TaskBucket, TaskPriority
from atlas.services import create_goal, create_task, list_tasks, tasks_done_in_week, update_task
from tests.services.helpers import seed_health


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


def test_task_can_link_to_a_goal(session):
    seed_health(session)
    create_goal(
        session,
        "this-week",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 8, 10),
        due_on=date(2026, 8, 16),
    )
    task = create_task(session, "Pushups", goal_slug="this-week")
    assert task.goal_id is not None
    assert [row.title for row in list_tasks(session, goal_slug="this-week")] == ["Pushups"]
    cleared = update_task(session, task.id, goal_slug=None)
    assert cleared.goal_id is None

