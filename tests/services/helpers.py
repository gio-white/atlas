from datetime import date

from atlas.domain import Aggregation, Comparator, Direction, Period, ValueType
from atlas.services import create_area, create_habit, create_metric, log_entry


def seed_health(session):
    area = create_area(session, "health", name="Health")
    pushups = create_metric(
        session,
        "pushups",
        area_slug="health",
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
        unit="reps",
    )
    weight = create_metric(
        session,
        "weight",
        area_slug="health",
        value_type=ValueType.QUANTITY,
        aggregation=Aggregation.LAST,
        direction=Direction.LOWER_IS_BETTER,
        unit="kg",
    )
    meditated = create_metric(
        session,
        "meditated",
        area_slug="health",
        value_type=ValueType.BOOL,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    return area, pushups, weight, meditated


def seed_daily_pushups(session, *, active_from: date = date(2026, 8, 1)):
    seed_health(session)
    return create_habit(
        session,
        "pushups-daily",
        metric_slug="pushups",
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        active_from=active_from,
    )


def log_pushups(session, day: date, value: float = 10.0):
    return log_entry(session, "pushups", value, occurred_on=day)
