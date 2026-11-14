from atlas.domain import Direction
from atlas.services import (
    archive_metric,
    create_metric,
    get_metric,
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


def test_archive_metric(session):
    create_metric(session, "pushups", value_type="count", aggregation="sum")
    archived = archive_metric(session, "pushups")
    assert archived.archived_at is not None
