from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from atlas.domain import ParentKind, TaskStatus, TimeBlockStatus
from atlas.domain.quests import QuestKind
from atlas.services import NotFoundError, ValidationError
from atlas.services.quest_views import plan_view, today_view
from atlas.services.quests import (
    complete_container,
    create_container,
    create_task,
    get_task,
    update_task,
)
from atlas.services.time_blocks import (
    cancel_time_block,
    complete_time_block,
    create_time_block,
    delete_time_block,
    get_time_block,
    list_time_blocks,
    miss_time_block,
    update_time_block,
)

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


@pytest.fixture(autouse=True)
def utc_zone(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def _task(session, title: str = "Study", **fields):
    return create_task(session, title=title, standalone=True, now=NOW, **fields)


def _block(session, task_id: int, start: datetime, hours: float = 1):
    end = start + timedelta(hours=hours)
    return create_time_block(session, task_id=task_id, start_at=start, end_at=end, now=NOW)


def test_create_converts_to_utc_and_lists_by_overlap(session):
    task = _task(session)
    plus_two = timezone(timedelta(hours=2))
    block = create_time_block(
        session,
        task_id=task.id,
        start_at=datetime(2026, 11, 8, 10, 0, tzinfo=plus_two),
        end_at=datetime(2026, 11, 8, 11, 30, tzinfo=plus_two),
        now=NOW,
    )
    assert block.start_at == datetime(2026, 11, 8, 8, 0, tzinfo=UTC)
    assert block.minutes == 90
    assert block.provider.value == "internal"
    other = _block(session, task.id, NOW + 5 * HOUR)
    window = list_time_blocks(session, start=NOW - 5 * HOUR, end=NOW, now=NOW)
    assert [item.id for item in window] == [block.id]
    assert [item.id for item in list_time_blocks(session, task_id=task.id)] == [block.id, other.id]


def test_create_rules(session):
    task = _task(session)
    with pytest.raises(ValidationError, match="end after"):
        create_time_block(session, task_id=task.id, start_at=NOW, end_at=NOW)
    with pytest.raises(ValidationError, match="does not exist"):
        create_time_block(session, task_id=999, start_at=NOW, end_at=NOW + HOUR)
    update_task(session, task.id, {"status": TaskStatus.COMPLETED}, now=NOW)
    with pytest.raises(ValidationError, match="reopen"):
        _block(session, task.id, NOW)
    update_task(session, task.id, {"status": TaskStatus.IN_PROGRESS}, now=NOW)
    assert _block(session, task.id, NOW).status is TimeBlockStatus.SCHEDULED


def test_move_resize_delete(session):
    task = _task(session)
    block = _block(session, task.id, NOW)
    moved = update_time_block(session, block.id, start_at=NOW + HOUR, end_at=NOW + 3 * HOUR)
    assert moved.minutes == 120
    resized = update_time_block(session, block.id, end_at=NOW + 2 * HOUR)
    assert resized.minutes == 60
    with pytest.raises(ValidationError):
        update_time_block(session, block.id, end_at=NOW)
    delete_time_block(session, block.id)
    with pytest.raises(NotFoundError):
        get_time_block(session, block.id)


def test_complete_and_cancel_never_complete_the_task(session):
    task = _task(session)
    first = _block(session, task.id, NOW - 2 * HOUR)
    second = _block(session, task.id, NOW + HOUR)
    assert get_time_block(session, first.id, now=NOW).unconfirmed is True
    completed = complete_time_block(session, first.id, now=NOW)
    assert completed.status is TimeBlockStatus.COMPLETED
    assert completed.unconfirmed is False
    assert get_task(session, task.id).status is TaskStatus.IN_PROGRESS
    cancelled = cancel_time_block(session, second.id, now=NOW)
    assert cancelled.status is TimeBlockStatus.CANCELLED
    read = get_task(session, task.id, now=NOW)
    assert read.status is TaskStatus.IN_PROGRESS
    assert read.block_count == 2
    assert read.planned_minutes == 60


def test_overlaps_are_marked(session):
    task = _task(session)
    a = _block(session, task.id, NOW)
    b = _block(session, task.id, NOW + timedelta(minutes=30))
    c = _block(session, task.id, NOW + 3 * HOUR)
    flags = {item.id: item.overlaps for item in list_time_blocks(session)}
    assert flags == {a.id: True, b.id: True, c.id: False}


def test_today_view(session):
    goal = create_container(session, QuestKind.GOAL, {"title": "Ship"}, now=NOW)
    side = create_container(session, QuestKind.SIDE_QUEST, {"title": "Taxes"}, now=NOW)
    writing = create_task(
        session, title="Write", parent_kind=ParentKind.GOAL, parent_id=goal.id, now=NOW
    )
    forms = create_task(
        session,
        title="Forms",
        parent_kind=ParentKind.SIDE_QUEST,
        parent_id=side.id,
        due_on=date(2026, 11, 8),
        now=NOW,
    )
    overdue = _task(session, "Overdue", due_on=date(2026, 11, 1))
    yesterday = _block(session, writing.id, NOW - 26 * HOUR)
    morning = _block(session, writing.id, NOW - 3 * HOUR)
    evening = _block(session, writing.id, NOW + 6 * HOUR)
    cancelled = _block(session, overdue.id, NOW + HOUR)
    cancel_time_block(session, cancelled.id, now=NOW)
    _block(session, writing.id, NOW + 30 * HOUR)

    view = today_view(session, as_of=date(2026, 11, 8), now=NOW)

    assert [item.block.id for item in view.blocks] == [morning.id, evening.id]
    assert view.blocks[0].task.path[0].title == "Ship"
    assert [item.block.id for item in view.unconfirmed] == [yesterday.id, morning.id]
    assert [task.title for task in view.due_today] == ["Overdue", "Forms"]
    assert [task.id for task in view.up_next] == [forms.id]


def test_today_view_uses_the_local_day(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "Europe/Copenhagen")
    task = _task(session)
    late = _block(session, task.id, datetime(2026, 11, 7, 23, 30, tzinfo=UTC))
    view = today_view(session, as_of=date(2026, 11, 8), now=NOW)
    assert [item.block.id for item in view.blocks] == [late.id]


def test_plan_view(session):
    task = _task(session)
    inside = _block(session, task.id, NOW)
    overlapping = _block(session, task.id, NOW + timedelta(minutes=30))
    _block(session, task.id, NOW + 72 * HOUR)
    view = plan_view(session, start=NOW - HOUR, end=NOW + 24 * HOUR, now=NOW)
    assert [item.block.id for item in view.blocks] == [inside.id, overlapping.id]
    assert all(item.block.overlaps for item in view.blocks)
    assert view.blocks[0].task.title == "Study"


def test_not_scheduled_yet_lists_next_actions_without_an_upcoming_session(session):
    goals = [
        create_container(session, QuestKind.GOAL, {"title": title}, now=NOW)
        for title in ("Ship", "Learn", "Move", "Read")
    ]
    side = create_container(session, QuestKind.SIDE_QUEST, {"title": "Taxes"}, now=NOW)
    done_goal = create_container(session, QuestKind.GOAL, {"title": "Done"}, now=NOW)

    def next_task(kind, parent, title):
        return create_task(session, title=title, parent_kind=kind, parent_id=parent.id, now=NOW)

    planned, past, cancelled, open_ = (
        next_task(ParentKind.GOAL, goal, title)
        for goal, title in zip(goals, ("Planned", "Past", "Cancelled", "Open"), strict=True)
    )
    forms = next_task(ParentKind.SIDE_QUEST, side, "Forms")
    next_task(ParentKind.GOAL, done_goal, "Leftover")
    complete_container(session, QuestKind.GOAL, done_goal.id, override=True, now=NOW)
    _block(session, planned.id, NOW + 50 * HOUR)  # upcoming, outside the week shown
    _block(session, past.id, NOW - 3 * HOUR)  # ended, unanswered: not upcoming
    later = _block(session, cancelled.id, NOW + 3 * HOUR)
    cancel_time_block(session, later.id, now=NOW)

    view = plan_view(session, start=NOW - HOUR, end=NOW + HOUR, now=NOW)

    assert [task.id for task in view.not_scheduled] == [past.id, cancelled.id, open_.id, forms.id]


def test_a_session_in_progress_counts_as_upcoming(session):
    goal = create_container(session, QuestKind.GOAL, {"title": "Ship"}, now=NOW)
    task = create_task(
        session, title="Write", parent_kind=ParentKind.GOAL, parent_id=goal.id, now=NOW
    )
    _block(session, task.id, NOW - timedelta(minutes=30))

    assert plan_view(session, start=NOW, end=NOW + HOUR, now=NOW).not_scheduled == []


def test_a_session_that_did_not_happen_is_kept_apart_from_a_cancelled_one(session):
    task = _task(session)
    past = _block(session, task.id, NOW - 3 * HOUR)
    later = _block(session, task.id, NOW + 3 * HOUR)

    missed = miss_time_block(session, past.id, now=NOW)

    assert missed.status is TimeBlockStatus.MISSED
    assert missed.unconfirmed is False
    assert get_task(session, task.id, now=NOW).status is TaskStatus.TODO
    with pytest.raises(ValidationError, match="not started"):
        miss_time_block(session, later.id, now=NOW)
    with pytest.raises(ValidationError, match="only a planned session"):
        miss_time_block(session, past.id, now=NOW)
    with pytest.raises(NotFoundError):
        miss_time_block(session, 9999, now=NOW)
    assert get_task(session, task.id, now=NOW).planned_minutes == 60
    day = today_view(session, as_of=NOW.date(), now=NOW)
    assert [item.block.id for item in day.unconfirmed] == []
    assert [item.block.id for item in day.blocks] == [past.id, later.id]
