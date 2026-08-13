from datetime import date

from atlas.domain import Comparator, Direction, GoalKind, GoalStatus, Period
from atlas.services import (
    MilestoneInput,
    archive_area,
    archive_metric,
    create_area,
    create_goal,
    create_habit,
    create_metric,
    get_area,
    get_goal_detail,
    get_habit,
    get_metric,
    list_areas,
    toggle_milestone,
    update_area,
    update_goal,
    update_habit,
    update_metric,
)


def test_update_and_archive_area(session):
    create_area(session, "health", name="Health")
    updated = update_area(session, "health", name="Wellness", description="body")
    assert updated.name == "Wellness"
    assert updated.description == "body"
    archived = archive_area(session, "health")
    assert archived.archived_at is not None
    assert list_areas(session) == []


def test_update_metric_display_fields(session):
    create_area(session, "health")
    create_metric(
        session,
        "weight",
        area_slug="health",
        value_type="quantity",
        aggregation="last",
        unit="kg",
    )
    updated = update_metric(
        session, "weight", name="Bodyweight", unit="lb", direction=Direction.LOWER_IS_BETTER
    )
    assert updated.name == "Bodyweight"
    assert updated.unit == "lb"
    assert Direction(updated.direction) is Direction.LOWER_IS_BETTER
    assert get_metric(session, "weight").aggregation == "last"


def test_update_habit_target_and_end_date(session):
    create_area(session, "health")
    create_metric(session, "pushups", area_slug="health", value_type="count", aggregation="sum")
    create_habit(
        session,
        "pushups-daily",
        metric_slug="pushups",
        period=Period.DAY,
        target_value=1,
        comparator=Comparator.AT_LEAST,
        active_from=date(2026, 8, 1),
    )
    updated = update_habit(
        session,
        "pushups-daily",
        target_value=20,
        weekdays=[1, 3, 5],
        active_to=date(2026, 12, 31),
    )
    assert updated.target_value == 20.0
    assert updated.weekdays == [1, 3, 5]
    assert updated.active_to == date(2026, 12, 31)
    assert get_habit(session, "pushups-daily").name == "Pushups Daily"


def test_update_goal_and_toggle_milestone(session):
    create_area(session, "health")
    create_goal(
        session,
        "ship",
        area_slug="health",
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
        milestones=[MilestoneInput(name="Hit 78kg")],
    )
    updated = update_goal(session, "ship", name="Ship it", status=GoalStatus.PAUSED)
    assert updated.name == "Ship it"
    assert GoalStatus(updated.status) is GoalStatus.PAUSED
    detail = get_goal_detail(session, "ship")
    assert [item.name for item in detail.milestones] == ["Hit 78kg"]
    toggled = toggle_milestone(session, "ship", "Hit 78kg")
    assert toggled.done_at is not None


def test_get_area_and_archive_metric(session):
    create_area(session, "health")
    create_metric(session, "pushups", area_slug="health", value_type="count", aggregation="sum")
    assert get_area(session, "health").slug == "health"
    archived = archive_metric(session, "pushups")
    assert archived.archived_at is not None
