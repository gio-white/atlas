from datetime import date

from atlas.domain import Comparator, Direction, Period
from atlas.services import (
    archive_metric,
    create_habit,
    create_metric,
    get_habit,
    get_metric,
    update_habit,
    update_metric,
)


def test_update_metric_display_fields(session):
    create_metric(
        session,
        "weight",
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
    create_metric(session, "pushups", value_type="count", aggregation="sum")
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


def test_archive_metric(session):
    create_metric(session, "pushups", value_type="count", aggregation="sum")
    archived = archive_metric(session, "pushups")
    assert archived.archived_at is not None
