from datetime import UTC, datetime

from sqlmodel import Session, select

from atlas.db.models import Metric
from atlas.domain import Aggregation, Direction, MetricOrigin, ValueType
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    not_archived,
    require_metric,
)
from atlas.services.slugs import display_name, normalize_slug, slug_from_name

_UNSET = object()


def create_metric(
    session: Session,
    slug: str | None = None,
    *,
    value_type: ValueType,
    aggregation: Aggregation,
    name: str | None = None,
    unit: str | None = None,
    direction: Direction = Direction.NEUTRAL,
    origin: MetricOrigin = MetricOrigin.MANUAL,
) -> Metric:
    """Create a metric. Without `slug` it is derived from `name`, so people only type a name."""
    if slug is None:
        if name is None or not name.strip():
            raise ValidationError("a metric needs a name or a slug")
        slug = slug_from_name(name)
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Metric, slug)
    metric = Metric(
        slug=slug,
        name=name.strip() if name is not None and name.strip() else display_name(slug),
        value_type=value_type,
        unit=unit,
        aggregation=aggregation,
        direction=direction,
        origin=origin,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def list_metrics(session: Session, *, include_archived: bool = False) -> list[Metric]:
    statement = select(Metric).order_by(Metric.slug)
    if not include_archived:
        statement = statement.where(not_archived(Metric.archived_at))
    return list(session.exec(statement).all())


def get_metric(session: Session, slug: str) -> Metric:
    return require_metric(session, normalize_slug(slug))


def archive_metric(session: Session, slug: str) -> Metric:
    metric = require_metric(session, normalize_slug(slug))
    if metric.archived_at is not None:
        raise ValidationError(f"metric {metric.slug!r} is already archived")
    metric.archived_at = datetime.now(UTC)
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def update_metric(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    unit: str | None | object = _UNSET,
    direction: Direction | None = None,
) -> Metric:
    metric = require_metric(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        metric.name = name
    if unit is not _UNSET:
        if unit is not None and not isinstance(unit, str):
            raise ValidationError("unit must be a string or None")
        metric.unit = unit
    if direction is not None:
        metric.direction = direction
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric
