"""Quest services over in-memory SQLite: acceptance criteria 1–21 of the quests brief."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlmodel import select

from atlas.db.models import Task
from atlas.domain import ChapterState, ParentKind, QuestStatus, TaskPriority, TaskStatus
from atlas.domain.quests import QuestKind
from atlas.services import ConflictError, NotFoundError, ValidationError
from atlas.services.quest_views import (
    goal_view,
    inbox_view,
    main_quests_view,
    side_quest_view,
    side_quests_view,
)
from atlas.services.quests import (
    complete_container,
    create_container,
    create_task,
    delete_container,
    delete_task,
    get_container,
    get_task,
    list_containers,
    list_tasks,
    organize_task,
    promote_task,
    reopen_container,
    update_container,
    update_task,
)
from atlas.services.time_blocks import complete_time_block, create_time_block

NOW = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)
A, G, M, S, C = (
    QuestKind.AMBITION,
    QuestKind.GOAL,
    QuestKind.MILESTONE,
    QuestKind.SIDE_QUEST,
    QuestKind.CHAPTER,
)


def make(session, kind: QuestKind, title: str, **fields):
    return create_container(session, kind, {"title": title, **fields}, now=NOW)


def task_in(session, kind: ParentKind | None, parent_id: int | None, title: str, **fields):
    return create_task(
        session, title=title, parent_kind=kind, parent_id=parent_id, now=NOW, **fields
    )


def done(session, task_id: int):
    return update_task(session, task_id, {"status": TaskStatus.COMPLETED}, now=NOW)


def test_criterion_1_ambition_without_goals(session):
    ambition = make(session, A, "Become a better engineer")
    assert ambition.progress is None
    assert ambition.goal_count == 0
    view = main_quests_view(session, now=NOW)
    assert [section.ambition.title for section in view.ambitions] == ["Become a better engineer"]
    assert view.ambitions[0].goals == []


def test_criterion_2_ambition_with_direct_tasks(session):
    ambition = make(session, A, "Health")
    read = task_in(session, ParentKind.AMBITION, ambition.id, "Read a book on sleep")
    task_in(session, ParentKind.AMBITION, ambition.id, "Book a check-up")
    done(session, read.id)
    view = get_container(session, A, ambition.id, now=NOW)
    assert (view.done_tasks, view.total_tasks, view.task_count) == (1, 2, 2)
    assert view.progress == 0.5
    section = main_quests_view(session, now=NOW).ambitions[0]
    assert [task.title for task in section.tasks] == ["Read a book on sleep", "Book a check-up"]
    assert section.tasks[0].path[0].kind is A


def test_criterion_3_goal_without_ambition(session):
    goal = make(session, G, "Run a marathon", due_on=date(2027, 4, 1))
    assert goal.ambition_id is None
    view = main_quests_view(session, now=NOW)
    assert [item.title for item in view.independent_goals] == ["Run a marathon"]


def test_criterion_4_goal_with_direct_tasks(session):
    goal = make(session, G, "Save 20,000")
    task = task_in(session, ParentKind.GOAL, goal.id, "Open a savings account")
    assert task.parent is not None and (task.parent.kind, task.parent.id) == (G, goal.id)
    assert goal_view(session, goal.id, now=NOW).tasks[0].id == task.id


def test_criterion_5_goal_with_milestones(session):
    goal = make(session, G, "Move to Copenhagen")
    first = make(session, M, "Find a job", goal_id=goal.id)
    second = make(session, M, "Find a flat", goal_id=goal.id)
    tree = goal_view(session, goal.id, now=NOW)
    assert [item.milestone.id for item in tree.milestones] == [first.id, second.id]
    assert tree.goal.milestone_count == 2
    assert tree.goal.progress == 0.0


def test_criterion_6_milestone_with_chapters_and_direct_tasks(session):
    goal = make(session, G, "Data engineering job")
    milestone = make(session, M, "Get hired", goal_id=goal.id)
    chapter = make(session, C, "Rust fundamentals", milestone_id=milestone.id)
    task_in(session, ParentKind.CHAPTER, chapter.id, "Understand ownership")
    task_in(session, ParentKind.MILESTONE, milestone.id, "Update CV")
    tree = goal_view(session, goal.id, now=NOW).milestones[0]
    assert [item.chapter.title for item in tree.chapters] == ["Rust fundamentals"]
    assert [task.title for task in tree.chapters[0].tasks] == ["Understand ownership"]
    assert [task.title for task in tree.tasks] == ["Update CV"]
    assert tree.milestone.total_tasks == 2


def test_criterion_7_chapter_with_multiple_tasks(session):
    side = make(session, S, "Taxes")
    chapter = make(session, C, "Papers", side_quest_id=side.id)
    ids = [task_in(session, ParentKind.CHAPTER, chapter.id, f"Paper {n}").id for n in range(3)]
    view = get_container(session, C, chapter.id, now=NOW)
    assert view.state is ChapterState.NOT_STARTED
    assert view.task_count == 3
    update_task(session, ids[0], {"status": TaskStatus.IN_PROGRESS}, now=NOW)
    assert get_container(session, C, chapter.id, now=NOW).state is ChapterState.IN_PROGRESS


def test_criterion_8_side_quest_with_chapters_and_direct_tasks(session):
    side = make(session, S, "Tax declaration")
    chapter = make(session, C, "Collect papers", side_quest_id=side.id)
    task_in(session, ParentKind.CHAPTER, chapter.id, "Find payslips")
    task_in(session, ParentKind.SIDE_QUEST, side.id, "Submit")
    tree = side_quest_view(session, side.id, now=NOW)
    assert [item.chapter.title for item in tree.chapters] == ["Collect papers"]
    assert [task.title for task in tree.tasks] == ["Submit"]
    assert [item.title for item in side_quests_view(session, now=NOW).side_quests] == [
        "Tax declaration"
    ]


def test_criterion_9_standalone_task_is_a_side_quest(session):
    task = create_task(session, title="Renew passport", standalone=True, now=NOW)
    assert task.standalone and not task.inbox
    view = side_quests_view(session, now=NOW)
    assert [item.title for item in view.standalone_tasks] == ["Renew passport"]
    assert inbox_view(session, now=NOW).count == 0


def test_criterion_10_inbox_capture_needs_only_a_title(session):
    first = create_task(session, title="Look into climbing gyms", now=NOW)
    second = create_task(session, title="Idea: blog", now=NOW + timedelta(minutes=1))
    assert first.inbox and first.organized_at is None and first.parent is None
    inbox = inbox_view(session, now=NOW)
    assert inbox.count == 2
    assert [task.id for task in inbox.tasks] == [second.id, first.id]


def test_criterion_11_move_inbox_task_into_a_chapter_without_duplicating(session):
    side = make(session, S, "Learn Rust")
    chapter = make(session, C, "Basics", side_quest_id=side.id)
    captured = create_task(session, title="Understand borrowing", now=NOW)
    later = NOW + timedelta(hours=1)
    organized = organize_task(
        session, captured.id, parent_kind=ParentKind.CHAPTER, parent_id=chapter.id, now=later
    )
    assert organized.id == captured.id
    assert organized.organized_at == later
    assert organized.parent is not None and organized.parent.id == chapter.id
    assert [item.id for item in organized.path] == [side.id, chapter.id]
    assert len(session.exec(select(Task)).all()) == 1
    assert inbox_view(session, now=later).count == 0


def test_criterion_12_move_between_parents_keeps_history(session):
    goal = make(session, G, "Ship")
    other = make(session, G, "Ship v2")
    task = task_in(session, ParentKind.GOAL, goal.id, "Write docs")
    update_task(session, task.id, {"status": TaskStatus.IN_PROGRESS}, now=NOW)
    end = NOW + timedelta(hours=1)
    block = create_time_block(session, task_id=task.id, start_at=NOW, end_at=end, now=NOW)
    first_organized = get_task(session, task.id).organized_at
    moved = organize_task(
        session,
        task.id,
        parent_kind=ParentKind.GOAL,
        parent_id=other.id,
        now=NOW + timedelta(days=1),
    )
    assert moved.id == task.id
    assert moved.status is TaskStatus.IN_PROGRESS
    assert moved.started_at == NOW
    assert moved.organized_at == first_organized
    assert [item.id for item in moved.blocks] == [block.id]
    assert get_container(session, G, goal.id, now=NOW).total_tasks == 0
    assert get_container(session, G, other.id, now=NOW).total_tasks == 1


def test_criterion_13_multiple_time_blocks_per_task(session):
    task = create_task(session, title="Study", standalone=True, now=NOW)
    for offset in (0, 2, 4):
        start = NOW + timedelta(hours=offset)
        create_time_block(
            session, task_id=task.id, start_at=start, end_at=start + timedelta(minutes=45)
        )
    read = get_task(session, task.id, now=NOW)
    assert read.block_count == 3
    assert read.planned_minutes == 135


def test_criterion_14_completing_a_block_leaves_the_task_in_progress(session):
    task = create_task(session, title="Write chapter one", standalone=True, now=NOW)
    end = NOW + timedelta(hours=1)
    block = create_time_block(session, task_id=task.id, start_at=NOW, end_at=end)
    completed = complete_time_block(session, block.id, now=end)
    assert completed.status.value == "completed"
    read = get_task(session, task.id, now=end)
    assert read.status is TaskStatus.IN_PROGRESS
    assert read.completed_at is None
    assert read.started_at == end


def test_criterion_15_chapter_completed_when_all_tasks_are(session):
    side = make(session, S, "Move")
    chapter = make(session, C, "Packing", side_quest_id=side.id)
    ids = [task_in(session, ParentKind.CHAPTER, chapter.id, f"Box {n}").id for n in range(2)]
    for task_id in ids:
        done(session, task_id)
    view = get_container(session, C, chapter.id, now=NOW)
    assert view.state is ChapterState.COMPLETED
    assert view.progress == 1.0


def test_criterion_16_empty_chapter_is_not_completed(session):
    side = make(session, S, "Taxes")
    chapter = make(session, C, "Later", side_quest_id=side.id)
    assert get_container(session, C, chapter.id, now=NOW).state is ChapterState.EMPTY
    view = get_container(session, S, side.id, now=NOW)
    assert view.eligible is False
    assert [item.id for item in view.open_children] == [chapter.id]


def test_criterion_17_milestone_completion_considers_chapters_and_direct_tasks(session):
    goal = make(session, G, "Ship")
    milestone = make(session, M, "Beta", goal_id=goal.id)
    chapter = make(session, C, "Build", milestone_id=milestone.id)
    in_chapter = task_in(session, ParentKind.CHAPTER, chapter.id, "Code")
    direct = task_in(session, ParentKind.MILESTONE, milestone.id, "Announce")
    done(session, in_chapter.id)
    view = get_container(session, M, milestone.id, now=NOW)
    assert view.eligible is False
    assert [(item.kind, item.id) for item in view.open_children] == [(QuestKind.TASK, direct.id)]
    with pytest.raises(ConflictError, match="override"):
        complete_container(session, M, milestone.id, now=NOW)
    done(session, direct.id)
    assert get_container(session, M, milestone.id, now=NOW).eligible is True
    completed = complete_container(session, M, milestone.id, now=NOW)
    assert completed.status is QuestStatus.COMPLETED
    assert completed.completed_with_open_items is False


def test_criterion_18_goal_completion_considers_milestones_and_direct_tasks(session):
    goal = make(session, G, "Ship")
    milestone = make(session, M, "Beta", goal_id=goal.id)
    task_in(session, ParentKind.MILESTONE, milestone.id, "Code")
    direct = task_in(session, ParentKind.GOAL, goal.id, "Party")
    done(session, direct.id)
    view = get_container(session, G, goal.id, now=NOW)
    assert [(item.kind, item.id) for item in view.open_children] == [(M, milestone.id)]
    complete_container(session, M, milestone.id, override=True, now=NOW)
    assert get_container(session, G, goal.id, now=NOW).eligible is True


def test_criterion_19_manual_goal_completion_preserves_open_children(session):
    goal = make(session, G, "Move")
    open_task = task_in(session, ParentKind.GOAL, goal.id, "Find a flat")
    task_in(session, ParentKind.GOAL, goal.id, "Learn Danish", priority=TaskPriority.HIGH)
    with pytest.raises(ConflictError):
        complete_container(session, G, goal.id, now=NOW)
    completed = complete_container(session, G, goal.id, override=True, now=NOW)
    assert completed.status is QuestStatus.COMPLETED
    assert completed.completed_at == NOW
    assert completed.completed_with_open_items is True
    assert completed.progress == 1.0
    assert get_task(session, open_task.id).status is TaskStatus.TODO
    reopened = reopen_container(session, G, goal.id, now=NOW)
    assert reopened.status is QuestStatus.ACTIVE
    assert reopened.completed_at is None
    assert reopened.progress == 0.0


def test_criterion_20_weighted_progress(session):
    goal = make(session, G, "Ship")
    heavy = make(session, M, "Build", goal_id=goal.id, weight=3)
    light = make(session, M, "Launch", goal_id=goal.id)
    a = task_in(session, ParentKind.MILESTONE, heavy.id, "A")
    task_in(session, ParentKind.MILESTONE, heavy.id, "B")
    task_in(session, ParentKind.MILESTONE, light.id, "C")
    done(session, a.id)
    view = get_container(session, G, goal.id, now=NOW)
    assert view.progress == pytest.approx(0.5 * 3 / 4)
    tree = goal_view(session, goal.id, now=NOW)
    assert [item.milestone.weight_share for item in tree.milestones] == [0.75, 0.25]


def test_criterion_21_missing_levels_cause_no_errors(session):
    ambition = make(session, A, "Grow")
    goal = make(session, G, "Ship", ambition_id=ambition.id)
    make(session, M, "Empty milestone", goal_id=goal.id)
    make(session, G, "Bare goal")
    side = make(session, S, "Bare side quest")
    make(session, C, "Empty chapter", side_quest_id=side.id)
    create_task(session, title="Loose", now=NOW)
    main = main_quests_view(session, now=NOW)
    assert main.ambitions[0].goals[0].progress == 0.0
    assert main.independent_goals[0].progress is None
    assert main.independent_goals[0].next_action is None
    goal_view(session, goal.id, now=NOW)
    side_quests_view(session, now=NOW)
    side_quest_view(session, side.id, now=NOW)


# --- Structure and errors --------------------------------------------------------------------


def test_invalid_and_archived_parents_are_rejected(session):
    goal = make(session, G, "Ship")
    with pytest.raises(ValidationError):
        make(session, M, "No goal")
    with pytest.raises(ValidationError, match="does not exist"):
        make(session, M, "Ghost", goal_id=999)
    with pytest.raises(ValidationError):
        make(session, C, "Both", milestone_id=1, side_quest_id=1)
    with pytest.raises(ValidationError):
        create_container(session, A, {"title": "Grow", "goal_id": goal.id}, now=NOW)
    update_container(session, G, goal.id, {"archived": True}, now=NOW)
    with pytest.raises(ValidationError, match="archived"):
        task_in(session, ParentKind.GOAL, goal.id, "Late")
    with pytest.raises(ValidationError, match="archived"):
        make(session, M, "Late", goal_id=goal.id)


def test_milestone_moves_only_between_goals_and_chapter_between_parents(session):
    first = make(session, G, "One")
    second = make(session, G, "Two")
    milestone = make(session, M, "Step", goal_id=first.id)
    moved = update_container(session, M, milestone.id, {"goal_id": second.id}, now=NOW)
    assert moved.goal_id == second.id
    with pytest.raises(ValidationError):
        update_container(session, M, milestone.id, {"goal_id": None}, now=NOW)
    side = make(session, S, "Side")
    chapter = make(session, C, "Batch", milestone_id=milestone.id)
    moved_chapter = update_container(session, C, chapter.id, {"side_quest_id": side.id}, now=NOW)
    assert (moved_chapter.milestone_id, moved_chapter.side_quest_id) == (None, side.id)


def test_delete_rules(session):
    goal = make(session, G, "Ship")
    milestone = make(session, M, "Beta", goal_id=goal.id)
    with pytest.raises(ConflictError):
        delete_container(session, G, goal.id)
    update_container(session, M, milestone.id, {"archived": True}, now=NOW)
    with pytest.raises(ConflictError):
        delete_container(session, G, goal.id)
    delete_container(session, M, milestone.id)
    delete_container(session, G, goal.id)
    with pytest.raises(NotFoundError):
        get_container(session, G, goal.id)

    inbox = create_task(session, title="Idea", now=NOW)
    standalone = create_task(session, title="Errand", standalone=True, now=NOW)
    with pytest.raises(ConflictError, match="Inbox"):
        delete_task(session, standalone.id)
    end = NOW + timedelta(hours=1)
    create_time_block(session, task_id=inbox.id, start_at=NOW, end_at=end)
    with pytest.raises(ConflictError, match="time blocks"):
        delete_task(session, inbox.id)
    clean = create_task(session, title="Throwaway", now=NOW)
    delete_task(session, clean.id)
    with pytest.raises(NotFoundError):
        get_task(session, clean.id)


def test_archive_and_unarchive_keep_completion(session):
    side = make(session, S, "Taxes")
    complete_container(session, S, side.id, override=True, now=NOW)
    archived = update_container(session, S, side.id, {"archived": True}, now=NOW)
    assert archived.status is QuestStatus.ARCHIVED
    assert archived.archived_at == NOW
    with pytest.raises(ValidationError, match="archived"):
        complete_container(session, S, side.id, override=True, now=NOW)
    assert list_containers(session, S) == []
    assert len(list_containers(session, S, include_archived=True)) == 1
    restored = update_container(session, S, side.id, {"archived": False}, now=NOW)
    assert restored.status is QuestStatus.COMPLETED


def test_task_status_transitions_through_the_service(session):
    task = create_task(session, title="Write", standalone=True, now=NOW)
    later = NOW + timedelta(hours=2)
    completed = update_task(session, task.id, {"status": TaskStatus.COMPLETED}, now=later)
    assert (completed.started_at, completed.completed_at) == (later, later)
    reopened = update_task(session, task.id, {"status": TaskStatus.TODO}, now=later)
    assert reopened.completed_at is None
    assert reopened.started_at == later
    with pytest.raises(ValidationError):
        update_task(session, task.id, {"estimate_minutes": 0}, now=NOW)
    with pytest.raises(ValidationError):
        update_task(session, task.id, {"weight": -1}, now=NOW)


def test_positions_append_and_order_children(session):
    goal = make(session, G, "Ship")
    first = task_in(session, ParentKind.GOAL, goal.id, "First")
    second = task_in(session, ParentKind.GOAL, goal.id, "Second")
    assert (first.position, second.position) == (0, 1)
    update_task(session, second.id, {"position": -1}, now=NOW)
    assert [task.title for task in goal_view(session, goal.id, now=NOW).tasks] == [
        "Second",
        "First",
    ]


def test_list_tasks_filters(session):
    goal = make(session, G, "Ship")
    in_goal = task_in(session, ParentKind.GOAL, goal.id, "In goal", due_on=date(2026, 11, 8))
    inbox = create_task(session, title="Inbox", now=NOW)
    standalone = create_task(session, title="Standalone", standalone=True, now=NOW)
    archived = create_task(session, title="Old", standalone=True, now=NOW)
    update_task(session, archived.id, {"archived": True}, now=NOW)

    def ids(**filters):
        return [task.id for task in list_tasks(session, **filters)]

    assert ids(parent_kind=ParentKind.GOAL, parent_id=goal.id) == [in_goal.id]
    assert ids(inbox=True) == [inbox.id]
    assert ids(standalone=True) == [standalone.id]
    assert ids(due_on=date(2026, 11, 8)) == [in_goal.id]
    assert archived.id in ids(include_archived=True)
    with pytest.raises(ValidationError):
        list_tasks(session, parent_kind=ParentKind.GOAL)


def test_promote_inbox_task_into_each_container(session):
    ambition_task = create_task(session, title="Grow", description="Long run", now=NOW)
    ambition = promote_task(session, ambition_task.id, kind=A, now=NOW)
    assert get_container(session, A, ambition.id).description == "Long run"
    with pytest.raises(NotFoundError):
        get_task(session, ambition_task.id)

    goal_task = create_task(session, title="Ship", now=NOW)
    goal = promote_task(
        session, goal_task.id, kind=G, parent_kind=ParentKind.AMBITION, parent_id=ambition.id
    )
    assert get_container(session, G, goal.id).ambition_id == ambition.id
    milestone = promote_task(
        session, create_task(session, title="Beta", now=NOW).id, kind=M, parent_id=goal.id
    )
    chapter = promote_task(
        session,
        create_task(session, title="Build", now=NOW).id,
        kind=C,
        parent_kind=ParentKind.MILESTONE,
        parent_id=milestone.id,
    )
    side = promote_task(session, create_task(session, title="Taxes", now=NOW).id, kind=S)
    assert [chapter.kind, side.kind] == [C, S]


def test_promote_is_refused_with_blocks_or_outside_the_inbox(session):
    task = create_task(session, title="Study", now=NOW)
    end = NOW + timedelta(hours=1)
    create_time_block(session, task_id=task.id, start_at=NOW, end_at=end)
    with pytest.raises(ValidationError, match="organize it instead"):
        promote_task(session, task.id, kind=G)
    standalone = create_task(session, title="Errand", standalone=True, now=NOW)
    with pytest.raises(ValidationError, match="Inbox"):
        promote_task(session, standalone.id, kind=G)
    loose = create_task(session, title="Beta", now=NOW)
    with pytest.raises(ValidationError):
        promote_task(session, loose.id, kind=M)
    assert get_task(session, loose.id).inbox


def test_next_action_on_container_views(session):
    goal = make(session, G, "Ship")
    later = task_in(session, ParentKind.GOAL, goal.id, "Later", due_on=date(2026, 12, 1))
    sooner = task_in(session, ParentKind.GOAL, goal.id, "Sooner", due_on=date(2026, 11, 10))
    assert get_container(session, G, goal.id, now=NOW).next_action.id == sooner.id
    start = NOW + timedelta(hours=1)
    create_time_block(session, task_id=later.id, start_at=start, end_at=start + timedelta(hours=1))
    view = get_container(session, G, goal.id, now=NOW)
    assert view.next_action is not None and view.next_action.id == later.id
    assert view.planned_minutes == 60
