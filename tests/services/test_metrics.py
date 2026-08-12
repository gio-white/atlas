import pytest

from atlas.domain import Aggregation, Direction, ValueType
from atlas.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    archive_area,
    archive_metric,
    create_area,
    create_metric,
    list_metrics,
)
from tests.services.helpers import seed_health


def test_create_metric_requires_an_area(session):
    with pytest.raises(NotFoundError, match="area"):
        create_metric(
            session,
            "pushups",
            area_slug="health",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
        )


def test_create_metric_on_archived_area_is_rejected(session):
    create_area(session, "health")
    archive_area(session, "health")

    with pytest.raises(ValidationError, match="archived"):
        create_metric(
            session,
            "pushups",
            area_slug="health",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
        )


def test_list_metrics_filters_by_area_and_hides_archived(session):
    seed_health(session)
    create_area(session, "career")
    create_metric(
        session,
        "shipped",
        area_slug="career",
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    archive_metric(session, "weight")

    health = [metric.slug for metric in list_metrics(session, area_slug="health")]
    assert health == ["meditated", "pushups"]
    assert [metric.slug for metric in list_metrics(session)] == [
        "meditated",
        "pushups",
        "shipped",
    ]


def test_duplicate_metric_slug_is_rejected(session):
    seed_health(session)

    with pytest.raises(AlreadyExistsError, match="pushups"):
        create_metric(
            session,
            "pushups",
            area_slug="health",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
        )


def test_metrics_of_an_archived_area_are_hidden(session):
    seed_health(session)
    archive_area(session, "health")

    assert list_metrics(session) == []
