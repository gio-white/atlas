from datetime import date

import pytest

from atlas.domain import Comparator, GoalKind, GoalStatus, Measure, PaceStatus
from atlas.services import (
    MilestoneInput,
    ValidationError,
    create_goal,
    get_goal,
    goal_progress,
    log_entry,
    toggle_milestone,
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
