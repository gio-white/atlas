from datetime import date

from sqlmodel import Session, select

from atlas.db.models import Area, Habit, Metric
from atlas.domain import Aggregation, Comparator, Direction, Period, ValueType
from atlas.services.errors import ValidationError
from atlas.services.habits import create_habit
from atlas.services.metrics import create_metric
from atlas.services.slugs import display_name

LIFE_AREA_SLUG = "life"
CHECKIN_METRIC_SLUG = "checkin"
CHECKIN_HABIT_SLUG = "checkin-daily"
SLIP_METRIC_SLUG = "slip"
JOURNAL_METRIC_SLUG = "journal"
SYSTEM_ACTIVE_FROM = date(2000, 1, 1)


def ensure_life_area(session: Session) -> Area:
    existing = session.exec(select(Area).where(Area.slug == LIFE_AREA_SLUG)).first()
    if existing is not None:
        if existing.archived_at is not None:
            raise ValidationError(f"area {LIFE_AREA_SLUG!r} is archived")
        return existing
    area = Area(
        slug=LIFE_AREA_SLUG,
        name="Life",
        description="Daily check-ins, slips, and journal.",
    )
    session.add(area)
    session.flush()
    return area


def ensure_life_metric(
    session: Session,
    slug: str,
    *,
    value_type: ValueType,
    aggregation: Aggregation,
    direction: Direction,
    unit: str | None = None,
    name: str | None = None,
) -> Metric:
    existing = session.exec(select(Metric).where(Metric.slug == slug)).first()
    if existing is not None:
        if existing.archived_at is not None:
            raise ValidationError(f"metric {slug!r} is archived")
        if ValueType(existing.value_type) is not value_type:
            raise ValidationError(
                f"metric {slug!r} exists with value_type {existing.value_type!r}; "
                f"expected {value_type}"
            )
        return existing
    ensure_life_area(session)
    return create_metric(
        session,
        slug,
        area_slug=LIFE_AREA_SLUG,
        value_type=value_type,
        aggregation=aggregation,
        direction=direction,
        unit=unit,
        name=name if name is not None else display_name(slug),
    )


def ensure_checkin_habit(session: Session) -> Habit:
    metric = ensure_life_metric(
        session,
        CHECKIN_METRIC_SLUG,
        value_type=ValueType.BOOL,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
        name="Check-in",
    )
    existing = session.exec(select(Habit).where(Habit.slug == CHECKIN_HABIT_SLUG)).first()
    if existing is not None:
        return existing
    return create_habit(
        session,
        CHECKIN_HABIT_SLUG,
        metric_slug=metric.slug,
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        name="Daily check-in",
        active_from=SYSTEM_ACTIVE_FROM,
    )
