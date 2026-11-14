from sqlmodel import Session, select

from atlas.db.models import Metric
from atlas.domain import Aggregation, Direction, MetricOrigin, ValueType
from atlas.services.errors import ValidationError
from atlas.services.metrics import create_metric
from atlas.services.slugs import display_name

JOURNAL_METRIC_SLUG = "journal"


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
    """The well-known metric behind the journal, created on first use and never set up by hand."""
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
    return create_metric(
        session,
        slug,
        value_type=value_type,
        aggregation=aggregation,
        direction=direction,
        unit=unit,
        name=name if name is not None else display_name(slug),
        origin=MetricOrigin.JOURNAL,
    )
