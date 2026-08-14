from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, col, select

from atlas.db.models import EntertainmentTitle, EntertainmentTitleTopic, EntertainmentTopic
from atlas.domain import (
    EntertainmentDashboardMath,
    EntertainmentKind,
    EntertainmentStatus,
    EntertainmentTitleView,
    EntertainmentTopicRef,
    Period,
    entertainment_dashboard_math,
    finished_in_week,
    last_finished,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    not_archived,
    require_entertainment_title,
    require_entertainment_topic,
)
from atlas.services.slugs import display_name, normalize_slug

_UNSET = object()
IMAGE_MAX_BYTES = 2 * 1024 * 1024
IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
_SUFFIX_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


@dataclass(frozen=True, slots=True)
class EntertainmentView:
    as_of: date
    in_progress: int
    finished_this_week: int
    last_finished: EntertainmentTitleView | None


def create_entertainment_topic(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> EntertainmentTopic:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, EntertainmentTopic, slug)
    topic = EntertainmentTopic(
        slug=slug,
        name=name if name is not None else display_name(slug),
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def list_entertainment_topics(
    session: Session,
    *,
    include_archived: bool = False,
) -> list[EntertainmentTopic]:
    statement = select(EntertainmentTopic).order_by(EntertainmentTopic.slug)
    if not include_archived:
        statement = statement.where(not_archived(EntertainmentTopic.archived_at))
    return list(session.exec(statement).all())


def get_entertainment_topic(session: Session, slug: str) -> EntertainmentTopic:
    return require_entertainment_topic(session, normalize_slug(slug))


def update_entertainment_topic(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> EntertainmentTopic:
    topic = require_entertainment_topic(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        topic.name = name
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def create_entertainment_title(
    session: Session,
    slug: str,
    *,
    kind: EntertainmentKind,
    name: str | None = None,
    creator: str | None = None,
    recommended_by: str | None = None,
    status: EntertainmentStatus = EntertainmentStatus.QUEUED,
    started_on: date | None = None,
    finished_on: date | None = None,
    progress: str | None = None,
    note: str | None = None,
    topics: list[str] | None = None,
    image_url: str | None = None,
) -> EntertainmentTitle:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, EntertainmentTitle, slug)
    kind = EntertainmentKind(kind)
    status = EntertainmentStatus(status)
    today = resolve_today(None)
    title = EntertainmentTitle(
        slug=slug,
        name=_require_name(name, slug),
        kind=kind,
        creator=_optional_text(creator, "creator"),
        recommended_by=_optional_text(recommended_by, "recommended_by"),
        status=status,
        started_on=started_on,
        finished_on=finished_on,
        progress=_optional_text(progress, "progress"),
        note=_optional_text(note, "note"),
        image_url=_validate_image_url(image_url) if image_url else None,
    )
    _stamp_status_dates(title, status, today)
    session.add(title)
    session.flush()
    _replace_title_topics(session, title, topics or [])
    session.commit()
    session.refresh(title)
    return title


def list_entertainment_titles(
    session: Session,
    *,
    kind: EntertainmentKind | None = None,
    status: EntertainmentStatus | None = None,
    topic: str | None = None,
    include_archived: bool = False,
) -> list[EntertainmentTitle]:
    statement = select(EntertainmentTitle).order_by(EntertainmentTitle.slug)
    if not include_archived:
        statement = statement.where(not_archived(EntertainmentTitle.archived_at))
    if kind is not None:
        statement = statement.where(EntertainmentTitle.kind == EntertainmentKind(kind))
    if status is not None:
        statement = statement.where(EntertainmentTitle.status == EntertainmentStatus(status))
    rows = list(session.exec(statement).all())
    if topic is None:
        return rows
    topic_row = require_entertainment_topic(session, normalize_slug(topic))
    linked_ids = {
        link.title_id
        for link in session.exec(
            select(EntertainmentTitleTopic).where(EntertainmentTitleTopic.topic_id == topic_row.id)
        ).all()
    }
    return [row for row in rows if row.id in linked_ids]


def get_entertainment_title(session: Session, slug: str) -> EntertainmentTitle:
    return require_entertainment_title(session, normalize_slug(slug))


def update_entertainment_title(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    kind: EntertainmentKind | None = None,
    creator: str | None | object = _UNSET,
    recommended_by: str | None | object = _UNSET,
    status: EntertainmentStatus | None = None,
    started_on: date | None | object = _UNSET,
    finished_on: date | None | object = _UNSET,
    progress: str | None | object = _UNSET,
    note: str | None | object = _UNSET,
    topics: list[str] | None = None,
    image_url: str | None | object = _UNSET,
) -> EntertainmentTitle:
    title = require_entertainment_title(session, normalize_slug(slug))
    if name is not None:
        title.name = _require_name(name, title.slug)
    if kind is not None:
        title.kind = EntertainmentKind(kind)
    if creator is not _UNSET:
        title.creator = _optional_text(creator if isinstance(creator, str) else None, "creator")
    if recommended_by is not _UNSET:
        title.recommended_by = _optional_text(
            recommended_by if isinstance(recommended_by, str) else None,
            "recommended_by",
        )
    if started_on is not _UNSET:
        if started_on is not None and not isinstance(started_on, date):
            raise ValidationError("started_on must be a date or None")
        title.started_on = started_on
    if finished_on is not _UNSET:
        if finished_on is not None and not isinstance(finished_on, date):
            raise ValidationError("finished_on must be a date or None")
        title.finished_on = finished_on
    if progress is not _UNSET:
        title.progress = _optional_text(progress if isinstance(progress, str) else None, "progress")
    if note is not _UNSET:
        title.note = _optional_text(note if isinstance(note, str) else None, "note")
    if status is not None:
        _stamp_status_dates(title, EntertainmentStatus(status), resolve_today(None))
    if topics is not None:
        _replace_title_topics(session, title, topics)
    if image_url is not _UNSET:
        _set_image_url(title, image_url if isinstance(image_url, str) else None)
    session.add(title)
    session.commit()
    session.refresh(title)
    return title


def set_title_image(
    session: Session,
    slug: str,
    data: bytes,
    *,
    media_type: str | None = None,
    filename: str | None = None,
) -> EntertainmentTitle:
    title = require_entertainment_title(session, normalize_slug(slug))
    resolved = _resolve_media_type(media_type, filename)
    if not data:
        raise ValidationError("image must not be empty")
    if len(data) > IMAGE_MAX_BYTES:
        raise ValidationError("image must be at most 2 MiB")
    title.image_bytes = data
    title.image_media_type = resolved
    title.image_url = None
    session.add(title)
    session.commit()
    session.refresh(title)
    return title


def clear_title_image(session: Session, slug: str) -> EntertainmentTitle:
    title = require_entertainment_title(session, normalize_slug(slug))
    title.image_bytes = None
    title.image_media_type = None
    title.image_url = None
    session.add(title)
    session.commit()
    session.refresh(title)
    return title


def get_title_image(session: Session, slug: str) -> tuple[bytes, str]:
    title = require_entertainment_title(session, normalize_slug(slug))
    if not title.image_bytes or not title.image_media_type:
        raise NotFoundError("entertainment_title_image", slug)
    return title.image_bytes, title.image_media_type


def title_image_href(title: EntertainmentTitle) -> str | None:
    if title.image_bytes:
        return f"/entertainment/titles/{title.slug}/image"
    return title.image_url


def title_topics(session: Session, title: EntertainmentTitle) -> list[EntertainmentTopic]:
    if title.id is None:
        return []
    topic_ids = [
        link.topic_id
        for link in session.exec(
            select(EntertainmentTitleTopic).where(EntertainmentTitleTopic.title_id == title.id)
        ).all()
    ]
    if not topic_ids:
        return []
    topics = list(
        session.exec(
            select(EntertainmentTopic).where(col(EntertainmentTopic.id).in_(topic_ids))
        ).all()
    )
    return sorted(topics, key=lambda topic: topic.slug)


def title_view_for(session: Session, title: EntertainmentTitle) -> EntertainmentTitleView:
    return _title_view(title, title_topics(session, title))


def entertainment_view(session: Session, *, as_of: date | None = None) -> EntertainmentView:
    as_of = resolve_today(as_of)
    titles = _title_views(session)
    return EntertainmentView(
        as_of=as_of,
        in_progress=sum(1 for title in titles if title.status is EntertainmentStatus.IN_PROGRESS),
        finished_this_week=finished_in_week(titles, as_of=as_of),
        last_finished=last_finished(titles, as_of=as_of),
    )


def entertainment_dashboard(
    session: Session,
    *,
    as_of: date | None = None,
    period: Period = Period.WEEK,
) -> EntertainmentDashboardMath:
    as_of = resolve_today(as_of)
    return entertainment_dashboard_math(_title_views(session), as_of=as_of, period=period)


def _title_views(session: Session) -> list[EntertainmentTitleView]:
    titles = list_entertainment_titles(session)
    topics_by_title = _topics_by_title_id(session)
    return [_title_view(title, topics_by_title.get(title.id or 0, [])) for title in titles]


def _title_view(
    title: EntertainmentTitle,
    topics: list[EntertainmentTopic],
) -> EntertainmentTitleView:
    return EntertainmentTitleView(
        slug=title.slug,
        name=title.name,
        kind=EntertainmentKind(title.kind),
        status=EntertainmentStatus(title.status),
        creator=title.creator,
        recommended_by=title.recommended_by,
        started_on=title.started_on,
        finished_on=title.finished_on,
        progress=title.progress,
        note=title.note,
        topics=tuple(EntertainmentTopicRef(slug=topic.slug, name=topic.name) for topic in topics),
        image=title_image_href(title),
    )


def _topics_by_title_id(session: Session) -> dict[int, list[EntertainmentTopic]]:
    topics = {topic.id: topic for topic in session.exec(select(EntertainmentTopic)).all()}
    grouped: dict[int, list[EntertainmentTopic]] = {}
    for link in session.exec(select(EntertainmentTitleTopic)).all():
        topic = topics.get(link.topic_id)
        if topic is None:
            continue
        grouped.setdefault(link.title_id, []).append(topic)
    for topic_list in grouped.values():
        topic_list.sort(key=lambda topic: topic.slug)
    return grouped


def _replace_title_topics(session: Session, title: EntertainmentTitle, slugs: list[str]) -> None:
    if title.id is None:
        raise ValidationError("title must be saved before topics can be attached")
    unique: list[str] = []
    seen: set[str] = set()
    for raw in slugs:
        slug = normalize_slug(raw)
        if slug in seen:
            continue
        seen.add(slug)
        unique.append(slug)
    topics = [require_entertainment_topic(session, slug) for slug in unique]
    for topic in topics:
        if topic.archived_at is not None:
            raise ValidationError(f"entertainment_topic {topic.slug!r} is archived")
    existing = list(
        session.exec(
            select(EntertainmentTitleTopic).where(EntertainmentTitleTopic.title_id == title.id)
        ).all()
    )
    for link in existing:
        session.delete(link)
    session.flush()
    for topic in topics:
        session.add(EntertainmentTitleTopic(title_id=title.id, topic_id=topic.id))


def _stamp_status_dates(
    title: EntertainmentTitle,
    status: EntertainmentStatus,
    today: date,
) -> None:
    title.status = status
    if status is EntertainmentStatus.IN_PROGRESS and title.started_on is None:
        title.started_on = today
    if status is EntertainmentStatus.DONE and title.finished_on is None:
        title.finished_on = today


def _set_image_url(title: EntertainmentTitle, image_url: str | None) -> None:
    if image_url is None or image_url == "":
        title.image_url = None
        title.image_bytes = None
        title.image_media_type = None
        return
    title.image_url = _validate_image_url(image_url)
    title.image_bytes = None
    title.image_media_type = None


def _validate_image_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned.startswith(("http://", "https://")):
        raise ValidationError("image_url must be an http or https URL")
    return cleaned


def _resolve_media_type(media_type: str | None, filename: str | None) -> str:
    candidate = (media_type or "").split(";")[0].strip().lower()
    if candidate == "image/jpg":
        candidate = "image/jpeg"
    if candidate in IMAGE_MEDIA_TYPES:
        return candidate
    if filename:
        suffix = ""
        lowered = filename.lower()
        for extension, mapped in _SUFFIX_MEDIA_TYPES.items():
            if lowered.endswith(extension):
                suffix = mapped
                break
        if suffix:
            return suffix
    raise ValidationError("image must be jpeg, png, webp, or gif")


def _require_name(name: str | None, slug: str) -> str:
    if name is None:
        return display_name(slug)
    cleaned = name.strip()
    if not cleaned:
        raise ValidationError("name must be a non-empty string")
    return cleaned


def _optional_text(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string or None")
    cleaned = value.strip()
    return cleaned or None
