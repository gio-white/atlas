from datetime import UTC, date, datetime, timedelta

import pytest

from atlas.domain import ChapterState, ParentKind, TaskPriority, TaskStatus, TimeBlockStatus
from atlas.domain.quests import (
    BlockView,
    ParentRef,
    QuestKind,
    QuestNode,
    QuestRuleError,
    TaskTimes,
    chapter_state,
    check_block_window,
    check_can_complete,
    check_can_schedule,
    check_parent,
    complete_block,
    completed_with_open_items,
    completion_check,
    is_unconfirmed,
    next_action,
    node_chapter_state,
    normalized_weights,
    overlapping_ids,
    planned_minutes,
    progress,
    task_counts,
    transition_task,
)

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
_ids = iter(range(1, 10_000))


def task(
    status: TaskStatus = TaskStatus.TODO,
    *,
    weight: float | None = None,
    position: int = 0,
    archived: bool = False,
    priority: TaskPriority = TaskPriority.NORMAL,
    due_on: date | None = None,
    blocks: tuple[BlockView, ...] = (),
    title: str = "",
) -> QuestNode:
    return QuestNode(
        kind=QuestKind.TASK,
        id=next(_ids),
        title=title,
        weight=weight,
        position=position,
        completed=status is TaskStatus.COMPLETED,
        archived=archived,
        status=status,
        priority=priority,
        due_on=due_on,
        blocks=blocks,
    )


def node(kind: QuestKind, *children: QuestNode, **fields) -> QuestNode:
    return QuestNode(kind=kind, id=next(_ids), children=tuple(children), **fields)


def block(
    start: datetime,
    minutes: int = 60,
    status: TimeBlockStatus = TimeBlockStatus.SCHEDULED,
) -> BlockView:
    return BlockView(
        id=next(_ids),
        task_id=0,
        start_at=start,
        end_at=start + timedelta(minutes=minutes),
        status=status,
    )


DONE = TaskStatus.COMPLETED
DOING = TaskStatus.IN_PROGRESS


# --- Structure -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("child", "parent"),
    [
        (QuestKind.GOAL, None),
        (QuestKind.GOAL, ParentKind.AMBITION),
        (QuestKind.MILESTONE, ParentKind.GOAL),
        (QuestKind.CHAPTER, ParentKind.MILESTONE),
        (QuestKind.CHAPTER, ParentKind.SIDE_QUEST),
        (QuestKind.TASK, None),
        (QuestKind.TASK, ParentKind.AMBITION),
        (QuestKind.TASK, ParentKind.GOAL),
        (QuestKind.TASK, ParentKind.MILESTONE),
        (QuestKind.TASK, ParentKind.CHAPTER),
        (QuestKind.TASK, ParentKind.SIDE_QUEST),
    ],
)
def test_allowed_parents(child, parent):
    check_parent(child, None if parent is None else ParentRef(parent, 1))


@pytest.mark.parametrize(
    ("child", "parent"),
    [
        (QuestKind.MILESTONE, None),
        (QuestKind.CHAPTER, None),
        (QuestKind.GOAL, ParentKind.GOAL),
        (QuestKind.GOAL, ParentKind.SIDE_QUEST),
        (QuestKind.MILESTONE, ParentKind.AMBITION),
        (QuestKind.MILESTONE, ParentKind.SIDE_QUEST),
        (QuestKind.CHAPTER, ParentKind.GOAL),
        (QuestKind.CHAPTER, ParentKind.CHAPTER),
        (QuestKind.AMBITION, ParentKind.AMBITION),
        (QuestKind.SIDE_QUEST, ParentKind.GOAL),
    ],
)
def test_invalid_parents_are_rejected(child, parent):
    with pytest.raises(QuestRuleError):
        check_parent(child, None if parent is None else ParentRef(parent, 1))


def test_archived_parent_takes_no_children():
    with pytest.raises(QuestRuleError, match="archived"):
        check_parent(QuestKind.TASK, ParentRef(ParentKind.CHAPTER, 3, archived=True))


# --- Task status -----------------------------------------------------------------------------


def test_leaving_todo_stamps_started_at_once():
    started = transition_task(TaskTimes(TaskStatus.TODO), DOING, NOW)
    assert started == TaskTimes(DOING, started_at=NOW)
    later = NOW + timedelta(days=1)
    back = transition_task(started, TaskStatus.TODO, later)
    assert back.started_at == NOW
    again = transition_task(back, DOING, later)
    assert again.started_at == NOW


def test_completion_sets_and_reopen_clears_completed_at():
    done = transition_task(TaskTimes(TaskStatus.TODO), DONE, NOW)
    assert (done.started_at, done.completed_at) == (NOW, NOW)
    still = transition_task(done, DONE, NOW + timedelta(hours=1))
    assert still.completed_at == NOW
    reopened = transition_task(done, TaskStatus.TODO, NOW + timedelta(hours=2))
    assert reopened.completed_at is None
    assert reopened.started_at == NOW


# --- Chapter state ---------------------------------------------------------------------------


def test_chapter_states():
    assert chapter_state([]) is ChapterState.EMPTY
    assert chapter_state([TaskStatus.TODO, TaskStatus.TODO]) is ChapterState.NOT_STARTED
    assert chapter_state([TaskStatus.TODO, DOING]) is ChapterState.IN_PROGRESS
    assert chapter_state([TaskStatus.TODO, DONE]) is ChapterState.IN_PROGRESS
    assert chapter_state([DONE, DONE]) is ChapterState.COMPLETED


def test_criterion_15_chapter_with_all_tasks_completed_is_completed():
    chapter = node(QuestKind.CHAPTER, task(DONE), task(DONE), task(DONE, archived=False))
    assert node_chapter_state(chapter) is ChapterState.COMPLETED


def test_criterion_16_empty_chapter_is_not_completed():
    empty = node(QuestKind.CHAPTER)
    only_archived = node(QuestKind.CHAPTER, task(DONE, archived=True))
    assert node_chapter_state(empty) is ChapterState.EMPTY
    assert node_chapter_state(only_archived) is ChapterState.EMPTY
    milestone = node(QuestKind.MILESTONE, empty)
    assert completion_check(milestone).eligible is False


# --- Completion ------------------------------------------------------------------------------


def test_criterion_17_milestone_considers_chapters_and_direct_tasks():
    done_chapter = node(QuestKind.CHAPTER, task(DONE))
    open_task = task(TaskStatus.TODO, title="Apply")
    milestone = node(QuestKind.MILESTONE, done_chapter, open_task)
    check = completion_check(milestone)
    assert check.eligible is False
    assert check.open_children == (open_task,)

    open_chapter = node(QuestKind.CHAPTER, task(DONE), task(DOING))
    milestone = node(QuestKind.MILESTONE, open_chapter, task(DONE))
    assert completion_check(milestone).open_children == (open_chapter,)

    milestone = node(QuestKind.MILESTONE, done_chapter, task(DONE))
    assert completion_check(milestone).eligible is True


def test_criterion_18_goal_considers_milestones_and_direct_tasks():
    done_milestone = node(QuestKind.MILESTONE, completed=True)
    goal = node(QuestKind.GOAL, done_milestone, task(TaskStatus.TODO))
    assert completion_check(goal).eligible is False
    open_milestone = node(QuestKind.MILESTONE, task(DONE))
    goal = node(QuestKind.GOAL, open_milestone, task(DONE))
    assert completion_check(goal).open_children == (open_milestone,)
    goal = node(QuestKind.GOAL, done_milestone, task(DONE))
    assert completion_check(goal).eligible is True


def test_ambition_considers_goals_and_direct_tasks():
    ambition = node(QuestKind.AMBITION, node(QuestKind.GOAL, completed=True), task(DONE))
    assert completion_check(ambition).eligible is True
    ambition = node(QuestKind.AMBITION, node(QuestKind.GOAL), task(DONE))
    assert completion_check(ambition).eligible is False


def test_archived_children_do_not_block_or_count():
    goal = node(QuestKind.GOAL, task(DONE), task(TaskStatus.TODO, archived=True))
    assert completion_check(goal).eligible is True
    assert completion_check(node(QuestKind.GOAL, task(DONE, archived=True))).eligible is False


def test_criterion_19_manual_completion_needs_override_and_reports_open_items():
    open_task = task(TaskStatus.TODO, title="Find a flat")
    goal = node(QuestKind.GOAL, task(DONE), open_task, title="Move")
    with pytest.raises(QuestRuleError, match="override"):
        check_can_complete(goal, override=False)
    check_can_complete(goal, override=True)
    completed = node(QuestKind.GOAL, task(DONE), open_task, completed=True)
    assert completed_with_open_items(completed) is True
    assert completion_check(completed).open_children == (open_task,)
    assert progress(completed) == 1.0


def test_completing_an_empty_container_needs_override():
    with pytest.raises(QuestRuleError, match="nothing"):
        check_can_complete(node(QuestKind.SIDE_QUEST), override=False)
    assert completed_with_open_items(node(QuestKind.SIDE_QUEST, completed=True)) is False


def test_chapters_and_archived_items_cannot_be_completed():
    with pytest.raises(QuestRuleError, match="chapter"):
        check_can_complete(node(QuestKind.CHAPTER, task(DONE)), override=True)
    with pytest.raises(QuestRuleError, match="archived"):
        check_can_complete(node(QuestKind.GOAL, task(DONE), archived=True), override=True)


def test_reaching_100_percent_never_completes():
    goal = node(QuestKind.GOAL, task(DONE))
    assert progress(goal) == 1.0
    assert goal.completed is False


# --- Progress --------------------------------------------------------------------------------


def test_progress_of_tasks_counts_in_progress_as_zero():
    assert progress(task(DONE)) == 1.0
    assert progress(task(DOING)) == 0.0
    assert progress(task(TaskStatus.TODO)) == 0.0


def test_container_without_children_is_not_broken_down_yet():
    assert progress(node(QuestKind.AMBITION)) is None
    assert progress(node(QuestKind.GOAL, task(DONE, archived=True))) is None


def test_criterion_20_weighted_progress():
    goal = node(
        QuestKind.GOAL,
        node(QuestKind.MILESTONE, task(DONE), task(TaskStatus.TODO), weight=3),
        task(DONE),
    )
    # milestone 0.5 × 3 + task 1 × 1 over 4
    assert progress(goal) == pytest.approx((0.5 * 3 + 1) / 4)


def test_missing_progress_counts_as_zero_inside_a_parent():
    goal = node(QuestKind.GOAL, node(QuestKind.MILESTONE), task(DONE))
    assert progress(goal) == 0.5


def test_completed_container_counts_as_one():
    ambition = node(
        QuestKind.AMBITION,
        node(QuestKind.GOAL, task(TaskStatus.TODO), completed=True),
        task(TaskStatus.TODO),
    )
    assert progress(ambition) == 0.5


def test_nested_chapter_progress():
    milestone = node(
        QuestKind.MILESTONE,
        node(QuestKind.CHAPTER, task(DONE), task(DONE), task(TaskStatus.TODO), task(DOING)),
        node(QuestKind.CHAPTER),
    )
    assert progress(milestone) == pytest.approx((0.5 + 0) / 2)


def test_normalized_weights_and_counts():
    children = [task(weight=3), task(), task(archived=True)]
    assert normalized_weights(children) == {0: 0.75, 1: 0.25}
    goal = node(
        QuestKind.GOAL,
        node(QuestKind.MILESTONE, task(DONE), task()),
        node(QuestKind.MILESTONE, task(DONE), archived=True),
        task(DONE),
    )
    counts = task_counts(goal)
    assert (counts.done, counts.total) == (2, 3)


def test_criterion_21_missing_levels_are_fine():
    shapes = [
        node(QuestKind.AMBITION),
        node(QuestKind.AMBITION, task(DONE)),
        node(QuestKind.AMBITION, node(QuestKind.GOAL)),
        node(QuestKind.GOAL, task()),
        node(QuestKind.GOAL, node(QuestKind.MILESTONE, task())),
        node(QuestKind.GOAL, node(QuestKind.MILESTONE, node(QuestKind.CHAPTER, task()))),
        node(QuestKind.SIDE_QUEST, task()),
        node(QuestKind.SIDE_QUEST, node(QuestKind.CHAPTER, task()), task()),
    ]
    for shape in shapes:
        progress(shape)
        completion_check(shape)
        next_action(shape, NOW)
        planned_minutes(shape)
        task_counts(shape)


# --- Next action -----------------------------------------------------------------------------


def test_next_action_prefers_the_earliest_upcoming_block():
    later = task(blocks=(block(NOW + timedelta(hours=3)),))
    sooner = task(DOING, blocks=(block(NOW + timedelta(hours=1)),))
    past = task(blocks=(block(NOW - timedelta(hours=3)),))
    cancelled = task(blocks=(block(NOW, status=TimeBlockStatus.CANCELLED),))
    goal = node(QuestKind.GOAL, later, sooner, past, cancelled)
    assert next_action(goal, NOW) is sooner


def test_next_action_counts_a_block_in_progress_now():
    running = task(blocks=(block(NOW - timedelta(minutes=30)),))
    goal = node(QuestKind.GOAL, task(blocks=(block(NOW + timedelta(hours=1)),)), running)
    assert next_action(goal, NOW) is running


def test_next_action_falls_back_to_first_in_progress_in_tree_order():
    first = task(DOING, position=0)
    second = task(DOING, position=1)
    milestone = node(QuestKind.MILESTONE, second, first, position=0)
    goal = node(QuestKind.GOAL, task(DOING, position=0), milestone)
    # containers come before direct tasks in tree order
    assert next_action(goal, NOW) is first


def test_next_action_then_todo_by_due_date_then_priority():
    undated_high = task(priority=TaskPriority.HIGH)
    due_later = task(due_on=date(2026, 11, 20), priority=TaskPriority.HIGH)
    due_soon_low = task(due_on=date(2026, 11, 10), priority=TaskPriority.LOW)
    due_soon_high = task(due_on=date(2026, 11, 10), priority=TaskPriority.HIGH, position=5)
    goal = node(QuestKind.GOAL, undated_high, due_later, due_soon_low, due_soon_high)
    assert next_action(goal, NOW) is due_soon_high


def test_next_action_none_when_everything_is_done():
    assert next_action(node(QuestKind.GOAL, task(DONE)), NOW) is None
    assert next_action(node(QuestKind.GOAL), NOW) is None


def test_completed_task_with_a_block_is_never_next():
    done = task(DONE, blocks=(block(NOW + timedelta(hours=1)),))
    todo = task()
    assert next_action(node(QuestKind.SIDE_QUEST, done, todo), NOW) is todo


# --- Time blocks -----------------------------------------------------------------------------


def test_planned_minutes_sums_non_cancelled_blocks_up_the_tree():
    goal = node(
        QuestKind.GOAL,
        node(
            QuestKind.MILESTONE,
            task(blocks=(block(NOW, 90), block(NOW, 30, TimeBlockStatus.CANCELLED))),
        ),
        task(blocks=(block(NOW, 45, TimeBlockStatus.COMPLETED),)),
        task(archived=True, blocks=(block(NOW, 600),)),
    )
    assert planned_minutes(goal) == 135


def test_unconfirmed_blocks():
    ended = block(NOW - timedelta(hours=2), 60)
    running = block(NOW - timedelta(minutes=30), 60)
    confirmed = block(NOW - timedelta(hours=2), 60, TimeBlockStatus.COMPLETED)
    assert is_unconfirmed(ended, NOW) is True
    assert is_unconfirmed(running, NOW) is False
    assert is_unconfirmed(confirmed, NOW) is False
    naive = BlockView(1, 1, datetime(2026, 11, 8, 9), datetime(2026, 11, 8, 10), ended.status)
    assert is_unconfirmed(naive, NOW) is True


def test_criterion_14_completing_a_block_moves_todo_to_in_progress_only():
    outcome = complete_block(TaskTimes(TaskStatus.TODO), NOW)
    assert outcome.block_status is TimeBlockStatus.COMPLETED
    assert outcome.task == TaskTimes(DOING, started_at=NOW)
    doing = TaskTimes(DOING, started_at=NOW - timedelta(days=1))
    assert complete_block(doing, NOW).task == doing
    done = TaskTimes(DONE, started_at=NOW, completed_at=NOW)
    assert complete_block(done, NOW).task == done


def test_block_window_and_scheduling_rules():
    with pytest.raises(QuestRuleError):
        check_block_window(NOW, NOW)
    check_block_window(NOW, NOW + timedelta(minutes=1))
    with pytest.raises(QuestRuleError, match="reopen"):
        check_can_schedule(DONE)
    with pytest.raises(QuestRuleError, match="archived"):
        check_can_schedule(TaskStatus.TODO, task_archived=True)
    check_can_schedule(DOING)


def test_overlapping_blocks_are_marked():
    a = block(NOW, 60)
    b = block(NOW + timedelta(minutes=30), 60)
    c = block(NOW + timedelta(hours=2), 30)
    d = block(NOW + timedelta(minutes=10), 10, TimeBlockStatus.CANCELLED)
    assert overlapping_ids([a, b, c, d]) == {a.id, b.id}
