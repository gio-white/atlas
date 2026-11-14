import pytest

from atlas.domain import Aggregation, Direction, MetricOrigin, ValueType
from atlas.services import (
    AlreadyExistsError,
    ValidationError,
    archive_metric,
    create_metric,
    list_metrics,
)
from tests.services.helpers import seed_health


def test_create_metric_is_manual_and_needs_no_grouping(session):
    metric = create_metric(
        session,
        "pushups",
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
    )

    assert metric.slug == "pushups"
    assert metric.name == "Pushups"
    assert MetricOrigin(metric.origin) is MetricOrigin.MANUAL


def test_create_metric_derives_its_slug_from_the_name(session):
    metric = create_metric(
        session,
        name="  Deep work (minutes) ",
        value_type=ValueType.DURATION,
        aggregation=Aggregation.SUM,
    )

    assert metric.slug == "deep-work-minutes"
    assert metric.name == "Deep work (minutes)"


def test_create_metric_needs_a_name_or_a_slug(session):
    with pytest.raises(ValidationError, match="name or a slug"):
        create_metric(session, value_type=ValueType.COUNT, aggregation=Aggregation.SUM)
    with pytest.raises(ValidationError, match="name or a slug"):
        create_metric(session, name="   ", value_type=ValueType.COUNT, aggregation=Aggregation.SUM)


def test_list_metrics_hides_archived(session):
    seed_health(session)
    create_metric(
        session,
        "shipped",
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    archive_metric(session, "weight")

    assert [metric.slug for metric in list_metrics(session)] == [
        "meditated",
        "pushups",
        "shipped",
    ]
    assert [metric.slug for metric in list_metrics(session, include_archived=True)] == [
        "meditated",
        "pushups",
        "shipped",
        "weight",
    ]


def test_duplicate_metric_slug_is_rejected(session):
    seed_health(session)

    with pytest.raises(AlreadyExistsError, match="pushups"):
        create_metric(
            session,
            "pushups",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
        )
    with pytest.raises(AlreadyExistsError, match="pushups"):
        create_metric(
            session, name="Pushups", value_type=ValueType.COUNT, aggregation=Aggregation.SUM
        )
