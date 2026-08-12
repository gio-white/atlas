from datetime import UTC, datetime

from sqlmodel import Session, select

from atlas.db.models import Area, Metric
from atlas.domain import Aggregation, Direction, ValueType
from atlas.services.errors import ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    not_archived,
    require_active_area,
    require_area,
    require_metric,
)
from atlas.services.slugs import display_name, normalize_slug


def create_metric(
    session: Session,
    slug: str,
    *,
    area_slug: str,
    value_type: ValueType,
    aggregation: Aggregation,
    name: str | None = None,
    unit: str | None = None,
    direction: Direction = Direction.NEUTRAL,
) -> Metric:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Metric, slug)
    area = require_active_area(session, normalize_slug(area_slug))
    metric = Metric(
        area_id=area.id,
        slug=slug,
        name=name if name is not None else display_name(slug),
        value_type=value_type,
        unit=unit,
        aggregation=aggregation,
        direction=direction,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def list_metrics(
    session: Session,
    *,
    area_slug: str | None = None,
    include_archived: bool = False,
) -> list[Metric]:
    statement = select(Metric).order_by(Metric.slug)
    if area_slug is not None:
        area = (
            require_area(session, normalize_slug(area_slug))
            if include_archived
            else require_active_area(session, normalize_slug(area_slug))
        )
        statement = statement.where(Metric.area_id == area.id)
    if not include_archived:
        statement = statement.where(not_archived(Metric.archived_at))
        statement = statement.join(Area).where(not_archived(Area.archived_at))
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
