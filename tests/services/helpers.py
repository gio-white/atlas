from datetime import date

from atlas.domain import Aggregation, Direction, HabitFrequency, ValueType
from atlas.services import RuleInput, create_habit, create_metric, log_entry


def seed_health(session):
    pushups = create_metric(
        session,
        "pushups",
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
        unit="reps",
    )
    weight = create_metric(
        session,
        "weight",
        value_type=ValueType.QUANTITY,
        aggregation=Aggregation.LAST,
        direction=Direction.LOWER_IS_BETTER,
        unit="kg",
    )
    meditated = create_metric(
        session,
        "meditated",
        value_type=ValueType.BOOL,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    return pushups, weight, meditated


def seed_daily_pushups(session, *, first_day: date = date(2026, 8, 1)):
    return create_habit(
        session,
        "Morning pushups",
        RuleInput(frequency=HabitFrequency.EVERY_DAY),
        slug="pushups-daily",
        first_day=first_day,
    )


def log_pushups(session, day: date, value: float = 10.0):
    return log_entry(session, "pushups", value, occurred_on=day)
