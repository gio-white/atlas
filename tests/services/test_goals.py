from datetime import date

import pytest

from atlas.domain import Comparator, GoalHorizon, GoalKind, GoalStatus, Measure, PaceStatus
from atlas.services import (
    MilestoneInput,
    ValidationError,
    create_area,
    create_goal,
    create_task,
    get_goal,
    goal_progress,
    goals_board,
    list_goals,
    log_entry,
    toggle_milestone,
    update_goal,
)
from tests.services.helpers import seed_health


def test_metric_target_progress_and_pace(session):
    seed_health(session)
    create_goal(
        session,
        "bodyweight-75",
        area_slug="health",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
        name="Bodyweight 75kg",
    )
    log_entry(session, "weight", 80.0, occurred_on=date(2026, 1, 1))
    log_entry(session, "weight", 78.0, occurred_on=date(2026, 6, 1))

    report = goal_progress(session, "bodyweight-75", as_of=date(2026, 7, 1))

    assert report.current == 78.0
    assert report.baseline == 80.0
    assert report.fraction == 0.4
    assert report.target_met is False
    assert report.pace is PaceStatus.BEHIND
    assert report.status is GoalStatus.ACTIVE


def test_meeting_the_target_marks_the_goal_achieved(session):
    seed_health(session)
    create_goal(
        session,
        "bodyweight-75",
        area_slug="health",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
    )
    log_entry(session, "weight", 80.0, occurred_on=date(2026, 1, 1))
    log_entry(session, "weight", 75.0, occurred_on=date(2026, 8, 1))

    report = goal_progress(session, "bodyweight-75", as_of=date(2026, 8, 1))

    assert report.target_met is True
    assert report.status is GoalStatus.ACHIEVED
    assert report.pace is PaceStatus.ACHIEVED
    stored = get_goal(session, "bodyweight-75")
    assert stored.status is GoalStatus.ACHIEVED
    assert stored.achieved_at is not None


def test_milestone_toggle_and_progress(session):
    seed_health(session)
    create_goal(
        session,
        "ship-atlas",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
        milestones=[
            MilestoneInput("outline"),
            MilestoneInput("draft"),
            MilestoneInput("ship"),
        ],
    )

    before = goal_progress(session, "ship-atlas", as_of=date(2026, 8, 1))
    assert before.fraction == 0.0
    assert before.target_met is False

    toggle_milestone(session, "ship-atlas", "outline")
    toggle_milestone(session, "ship-atlas", "draft")
    mid = goal_progress(session, "ship-atlas", as_of=date(2026, 8, 1))
    assert mid.fraction == pytest.approx(2 / 3)
    assert mid.status is GoalStatus.ACTIVE

    toggle_milestone(session, "ship-atlas", "ship")
    done = goal_progress(session, "ship-atlas", as_of=date(2026, 8, 1))
    assert done.fraction == 1.0
    assert done.target_met is True
    assert done.status is GoalStatus.ACHIEVED


def test_toggle_milestone_can_reopen(session):
    seed_health(session)
    create_goal(
        session,
        "ship-atlas",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
        milestones=[MilestoneInput("outline")],
    )
    toggle_milestone(session, "ship-atlas", "outline")
    reopened = toggle_milestone(session, "ship-atlas", "outline")

    assert reopened.done_at is None


def test_metric_target_requires_metric_fields(session):
    seed_health(session)

    with pytest.raises(ValidationError, match="metric_target"):
        create_goal(
            session,
            "incomplete",
            area_slug="health",
            kind=GoalKind.METRIC_TARGET,
            start_on=date(2026, 1, 1),
            due_on=date(2026, 12, 31),
        )


def test_due_on_before_start_on_is_rejected(session):
    seed_health(session)

    with pytest.raises(ValidationError, match="due_on"):
        create_goal(
            session,
            "backwards",
            area_slug="health",
            kind=GoalKind.MILESTONE,
            start_on=date(2026, 12, 31),
            due_on=date(2026, 1, 1),
        )


def test_create_goal_infers_horizon_and_accepts_optional_parent(session):
    seed_health(session)
    long_goal = create_goal(
        session,
        "durable-health",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
        description="Stay strong.",
    )
    assert long_goal.horizon is GoalHorizon.LONG
    medium = create_goal(
        session,
        "bodyweight-75",
        area_slug="health",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 6, 1),
        parent_slug="durable-health",
    )
    assert medium.horizon is GoalHorizon.MEDIUM
    assert medium.parent_id == long_goal.id
    short = create_goal(
        session,
        "workout-week",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 8, 10),
        due_on=date(2026, 8, 16),
        parent_slug="bodyweight-75",
        horizon=GoalHorizon.SHORT,
    )
    assert short.parent_id == medium.id
    assert [goal.slug for goal in list_goals(session, parent_slug="durable-health")] == [
        "bodyweight-75"
    ]
    assert [goal.slug for goal in list_goals(session, horizon=GoalHorizon.SHORT)] == [
        "workout-week"
    ]


def test_long_goal_cannot_have_a_parent(session):
    seed_health(session)
    create_goal(
        session,
        "north",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
    )
    with pytest.raises(ValidationError, match="parent"):
        create_goal(
            session,
            "other-north",
            area_slug="health",
            kind=GoalKind.MILESTONE,
            start_on=date(2026, 1, 1),
            due_on=date(2028, 1, 1),
            parent_slug="north",
        )


def test_short_goal_cannot_parent_under_long(session):
    seed_health(session)
    create_goal(
        session,
        "north",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
    )
    with pytest.raises(ValidationError, match="short"):
        create_goal(
            session,
            "this-week",
            area_slug="health",
            kind=GoalKind.MILESTONE,
            start_on=date(2026, 8, 10),
            due_on=date(2026, 8, 16),
            parent_slug="north",
        )


def test_cannot_change_horizon_while_goal_has_children(session):
    seed_health(session)
    create_goal(
        session,
        "north",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
    )
    create_goal(
        session,
        "mid",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 6, 1),
        parent_slug="north",
    )
    with pytest.raises(ValidationError, match="children"):
        update_goal(session, "north", horizon=GoalHorizon.MEDIUM)


def test_goals_board_groups_by_horizon_and_lists_week_tasks(session):
    seed_health(session)
    create_goal(
        session,
        "north",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
        milestones=[MilestoneInput("keep going")],
    )
    create_goal(
        session,
        "mid",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 6, 1),
        parent_slug="north",
        milestones=[MilestoneInput("checkpoint")],
    )
    create_goal(
        session,
        "this-week",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 8, 10),
        due_on=date(2026, 8, 16),
        parent_slug="mid",
        milestones=[MilestoneInput("four sessions")],
    )
    create_task(session, "Pushups", goal_slug="this-week", due_on=date(2026, 8, 14))
    board = goals_board(session, as_of=date(2026, 8, 14))
    assert [goal.slug for goal in board.long.goals] == ["north"]
    assert [goal.slug for goal in board.medium.goals] == ["mid"]
    assert [goal.slug for goal in board.short.goals] == ["this-week"]
    assert board.week.total == 1
    assert board.week.done == 0
    assert board.week.tasks[0].goal == "this-week"
    assert board.long.total == 1
    assert board.long.on_track == 0


def test_create_goal_without_area(session):
    seed_health(session)
    goal = create_goal(
        session,
        "north",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
    )
    assert goal.area_id is None
    metric = create_goal(
        session,
        "bodyweight-75",
        kind=GoalKind.METRIC_TARGET,
        metric_slug="weight",
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
    )
    assert metric.area_id is None


def test_metric_must_match_area_only_when_both_are_set(session):
    seed_health(session)
    create_area(session, "finance", name="Finance")
    with pytest.raises(ValidationError, match="does not belong"):
        create_goal(
            session,
            "bodyweight-75",
            area_slug="finance",
            kind=GoalKind.METRIC_TARGET,
            metric_slug="weight",
            target_value=75.0,
            comparator=Comparator.AT_MOST,
            measure=Measure.LATEST_VALUE,
            start_on=date(2026, 1, 1),
            due_on=date(2026, 12, 31),
        )


def test_update_goal_can_clear_area(session):
    seed_health(session)
    create_goal(
        session,
        "north",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2028, 1, 1),
    )
    updated = update_goal(session, "north", area_slug=None)
    assert updated.area_id is None
    listed = list_goals(session, area_slug="health")
    assert listed == []
