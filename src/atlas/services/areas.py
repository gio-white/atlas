from datetime import UTC, datetime

from sqlmodel import Session, select

from atlas.db.models import Area
from atlas.services.errors import ValidationError
from atlas.services.lookups import ensure_unique_slug, not_archived, require_area
from atlas.services.slugs import display_name, normalize_slug

_UNSET = object()


def create_area(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Area:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, Area, slug)
    area = Area(
        slug=slug,
        name=name if name is not None else display_name(slug),
        description=description,
    )
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


def list_areas(session: Session, *, include_archived: bool = False) -> list[Area]:
    statement = select(Area).order_by(Area.slug)
    if not include_archived:
        statement = statement.where(not_archived(Area.archived_at))
    return list(session.exec(statement).all())


def get_area(session: Session, slug: str) -> Area:
    return require_area(session, normalize_slug(slug))


def archive_area(session: Session, slug: str) -> Area:
    area = require_area(session, normalize_slug(slug))
    if area.archived_at is not None:
        raise ValidationError(f"area {area.slug!r} is already archived")
    area.archived_at = datetime.now(UTC)
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


def update_area(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    description: str | None | object = _UNSET,
) -> Area:
    area = require_area(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        area.name = name
    if description is not _UNSET:
        if description is not None and not isinstance(description, str):
            raise ValidationError("description must be a string or None")
        area.description = description
    session.add(area)
    session.commit()
    session.refresh(area)
    return area
