from datetime import UTC, datetime

import pytest

from atlas.db import create_memory_engine, init_schema, make_session_factory
from atlas.domain import HabitFrequency, ParentKind
from atlas.domain.quests import QuestKind
from atlas.services import (
    ConflictError,
    NotFoundError,
    RuleInput,
    ValidationError,
    add_habit_support,
    archive_habit,
    create_habit,
    delete_habit,
    export_all,
    habits_supporting,
    import_all,
    list_habit_supports,
    remove_habit_support,
)
from atlas.services.quests import (
    create_container,
    create_task,
    delete_container,
    delete_task,
    get_container,
    promote_task,
    update_container,
)

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
A, G, M, S, C, T = (
    QuestKind.AMBITION,
    QuestKind.GOAL,
    QuestKind.MILESTONE,
    QuestKind.SIDE_QUEST,
    QuestKind.CHAPTER,
    QuestKind.TASK,
)


def _habit(session, slug: str, name: str):
    return create_habit(session, name, RuleInput(frequency=HabitFrequency.EVERY_DAY), slug=slug)


def _tree(session) -> dict[QuestKind, int]:
    """Ambition › Goal › Milestone › Chapter › Task, plus a side quest."""
    ambition = create_container(session, A, {"title": "Become an engineer"}, now=NOW)
    goal = create_container(session, G, {"title": "Ship Rust", "ambition_id": ambition.id})
    milestone = create_container(session, M, {"title": "Backend", "goal_id": goal.id})
    chapter = create_container(session, C, {"title": "Basics", "milestone_id": milestone.id})
    task = create_task(
        session, title="Read the book", parent_kind=ParentKind.CHAPTER, parent_id=chapter.id
    )
    side_quest = create_container(session, S, {"title": "Plan the trip"})
    return {
        A: ambition.id,
        G: goal.id,
        M: milestone.id,
        C: chapter.id,
        T: task.id,
        S: side_quest.id,
    }


def test_a_habit_can_support_an_item_at_every_level(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    for kind in (T, C, M, G, A, S):
        add_habit_support(session, "read", kind, ids[kind])

    supported = list_habit_supports(session, "read")

    assert [(item.kind, item.title) for item in supported] == [
        (A, "Become an engineer"),
        (G, "Ship Rust"),
        (M, "Backend"),
        (S, "Plan the trip"),
        (C, "Basics"),
        (T, "Read the book"),
    ]
    task = supported[-1]
    assert [ref.title for ref in task.path] == [
        "Become an engineer",
        "Ship Rust",
        "Backend",
        "Basics",
    ]
    assert supported[0].path == []


def test_an_item_lists_habits_linked_to_it_or_to_anything_under_it(session):
    _habit(session, "read", "Read")
    _habit(session, "code", "Code daily")
    _habit(session, "walk", "Walk")
    ids = _tree(session)
    add_habit_support(session, "code", G, ids[G])
    add_habit_support(session, "read", C, ids[C])
    add_habit_support(session, "read", T, ids[T])
    add_habit_support(session, "walk", S, ids[S])

    on_goal = habits_supporting(session, G, ids[G])
    assert [(row.slug, row.linked_to.kind, row.direct) for row in on_goal] == [
        ("code", G, True),
        ("read", C, False),
        ("read", T, False),
    ]
    on_ambition = habits_supporting(session, A, ids[A])
    assert {row.slug for row in on_ambition} == {"code", "read"}
    assert not any(row.direct for row in on_ambition)
    on_chapter = habits_supporting(session, C, ids[C])
    assert [(row.slug, row.direct) for row in on_chapter] == [("read", True), ("read", False)]
    assert [row.slug for row in habits_supporting(session, S, ids[S])] == ["walk"]
    assert habits_supporting(session, M, ids[M])[0].linked_to.title == "Basics"


def test_linking_changes_no_progress_weight_or_next_action(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    before = {kind: get_container(session, kind, ids[kind]) for kind in (A, G, M, C, S)}

    for kind in (A, G, M, C, T, S):
        add_habit_support(session, "read", kind, ids[kind])

    for kind, view in before.items():
        after = get_container(session, kind, ids[kind])
        assert after.progress == view.progress
        assert after.weight_share == view.weight_share
        assert after.eligible == view.eligible
        assert after.next_action == view.next_action


def test_add_refuses_duplicates_archived_items_and_archived_habits(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    add_habit_support(session, "read", G, ids[G])
    with pytest.raises(ConflictError, match="already supports"):
        add_habit_support(session, "read", G, ids[G])
    with pytest.raises(NotFoundError):
        add_habit_support(session, "read", M, 999)
    update_container(session, S, ids[S], {"archived": True})
    with pytest.raises(ValidationError, match="archived"):
        add_habit_support(session, "read", S, ids[S])
    archive_habit(session, "read")
    with pytest.raises(ValidationError, match="restore it first"):
        add_habit_support(session, "read", A, ids[A])
    # An archived habit keeps its links and can still drop them.
    remove_habit_support(session, "read", G, ids[G])
    assert list_habit_supports(session, "read") == []


def test_remove_drops_one_link(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    add_habit_support(session, "read", G, ids[G])
    add_habit_support(session, "read", C, ids[C])

    remove_habit_support(session, "read", G, ids[G])

    assert [item.kind for item in list_habit_supports(session, "read")] == [C]
    with pytest.raises(NotFoundError):
        remove_habit_support(session, "read", G, ids[G])


def test_deleting_a_habit_or_an_item_drops_its_links(session):
    _habit(session, "read", "Read")
    _habit(session, "walk", "Walk")
    side_quest = create_container(session, S, {"title": "Trip"})
    inbox = create_task(session, title="Someday")
    add_habit_support(session, "read", S, side_quest.id)
    add_habit_support(session, "read", T, inbox.id)
    add_habit_support(session, "walk", S, side_quest.id)

    delete_container(session, S, side_quest.id)
    delete_task(session, inbox.id)
    assert list_habit_supports(session, "read") == []

    goal = create_container(session, G, {"title": "Ship"})
    add_habit_support(session, "walk", G, goal.id)
    delete_habit(session, "walk")
    assert habits_supporting(session, G, goal.id) == []


def test_promoting_an_inbox_task_keeps_its_habit_links(session):
    _habit(session, "read", "Read")
    task = create_task(session, title="Learn Go")
    add_habit_support(session, "read", T, task.id)

    goal = promote_task(session, task.id, kind=G)

    assert [(item.kind, item.id) for item in list_habit_supports(session, "read")] == [(G, goal.id)]


def test_export_round_trips_links_at_every_level(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    for kind in (A, G, M, C, T, S):
        add_habit_support(session, "read", kind, ids[kind])
    payload = export_all(session)
    assert {row["kind"] for row in payload["habit_supports"]} == {
        "ambition",
        "goal",
        "milestone",
        "chapter",
        "task",
        "side_quest",
    }

    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as fresh:
        import_all(fresh, payload)
        restored = list_habit_supports(fresh, "read")
        assert [(item.kind, item.title) for item in restored] == [
            (item.kind, item.title) for item in list_habit_supports(session, "read")
        ]
        assert [ref.title for ref in restored[-1].path][-1] == "Basics"


def test_import_replace_clears_links(session):
    _habit(session, "read", "Read")
    ids = _tree(session)
    add_habit_support(session, "read", G, ids[G])
    payload = export_all(session)

    import_all(session, payload, replace=True)

    assert len(list_habit_supports(session, "read")) == 1
