from datetime import date

from sqlmodel import Session, col, select

from atlas.db.models import LibraryTitle, LibraryTitleTopic, LibraryTopic
from atlas.domain import (
    LibraryDashboardMath,
    LibraryKind,
    LibraryStatus,
    LibraryTitleView,
    LibraryTopicRef,
    Period,
    library_dashboard_math,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    not_archived,
    require_library_title,
    require_library_topic,
)
from atlas.services.slugs import display_name, normalize_slug

_UNSET = object()
RATING_MIN = 1
RATING_MAX = 5
IMAGE_MAX_BYTES = 2 * 1024 * 1024
IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
_SUFFIX_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def create_library_topic(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> LibraryTopic:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, LibraryTopic, slug)
    topic = LibraryTopic(
        slug=slug,
        name=name if name is not None else display_name(slug),
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def list_library_topics(
    session: Session,
    *,
    include_archived: bool = False,
) -> list[LibraryTopic]:
    statement = select(LibraryTopic).order_by(LibraryTopic.slug)
    if not include_archived:
        statement = statement.where(not_archived(LibraryTopic.archived_at))
    return list(session.exec(statement).all())


def get_library_topic(session: Session, slug: str) -> LibraryTopic:
    return require_library_topic(session, normalize_slug(slug))


def update_library_topic(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
) -> LibraryTopic:
    topic = require_library_topic(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must be a non-empty string")
        topic.name = name
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def create_library_title(
    session: Session,
    slug: str,
    *,
    kind: LibraryKind,
    name: str | None = None,
    creator: str | None = None,
    recommended_by: str | None = None,
    status: LibraryStatus = LibraryStatus.QUEUED,
    started_on: date | None = None,
    finished_on: date | None = None,
    progress: str | None = None,
    note: str | None = None,
    rating: int | None = None,
    link: str | None = None,
    topics: list[str] | None = None,
    image_url: str | None = None,
) -> LibraryTitle:
    slug = normalize_slug(slug)
    ensure_unique_slug(session, LibraryTitle, slug)
    kind = LibraryKind(kind)
    status = LibraryStatus(status)
    today = resolve_today(None)
    title = LibraryTitle(
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
        rating=_validate_rating(rating),
        link=_validate_link(link),
        image_url=_validate_image_url(image_url) if image_url else None,
    )
    _stamp_status_dates(title, status, today)
    session.add(title)
    session.flush()
    _replace_title_topics(session, title, topics or [])
    session.commit()
    session.refresh(title)
    return title


def list_library_titles(
    session: Session,
    *,
    kind: LibraryKind | None = None,
    status: LibraryStatus | None = None,
    topic: str | None = None,
    include_archived: bool = False,
) -> list[LibraryTitle]:
    statement = select(LibraryTitle).order_by(LibraryTitle.slug)
    if not include_archived:
        statement = statement.where(not_archived(LibraryTitle.archived_at))
    if kind is not None:
        statement = statement.where(LibraryTitle.kind == LibraryKind(kind))
    if status is not None:
        statement = statement.where(LibraryTitle.status == LibraryStatus(status))
    rows = list(session.exec(statement).all())
    if topic is None:
        return rows
    topic_row = require_library_topic(session, normalize_slug(topic))
    linked_ids = {
        link.title_id
        for link in session.exec(
            select(LibraryTitleTopic).where(LibraryTitleTopic.topic_id == topic_row.id)
        ).all()
    }
    return [row for row in rows if row.id in linked_ids]


def get_library_title(session: Session, slug: str) -> LibraryTitle:
    return require_library_title(session, normalize_slug(slug))


def update_library_title(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    kind: LibraryKind | None = None,
    creator: str | None | object = _UNSET,
    recommended_by: str | None | object = _UNSET,
    status: LibraryStatus | None = None,
    started_on: date | None | object = _UNSET,
    finished_on: date | None | object = _UNSET,
    progress: str | None | object = _UNSET,
    note: str | None | object = _UNSET,
    rating: int | None | object = _UNSET,
    link: str | None | object = _UNSET,
    topics: list[str] | None = None,
    image_url: str | None | object = _UNSET,
) -> LibraryTitle:
    title = require_library_title(session, normalize_slug(slug))
    if name is not None:
        title.name = _require_name(name, title.slug)
    if kind is not None:
        title.kind = LibraryKind(kind)
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
    if rating is not _UNSET:
        title.rating = _validate_rating(rating)
    if link is not _UNSET:
        title.link = _validate_link(link)
    if status is not None:
        _stamp_status_dates(title, LibraryStatus(status), resolve_today(None))
    if topics is not None:
        _replace_title_topics(session, title, topics)
    if image_url is not _UNSET:
        _set_image_url(title, image_url if isinstance(image_url, str) else None)
    session.add(title)
    session.commit()
    session.refresh(title)
    return title


def delete_library_title(session: Session, slug: str) -> None:
    title = require_library_title(session, normalize_slug(slug))
    for link in session.exec(
        select(LibraryTitleTopic).where(LibraryTitleTopic.title_id == title.id)
    ).all():
        session.delete(link)
    session.flush()
    session.delete(title)
    session.commit()


def set_title_image(
    session: Session,
    slug: str,
    data: bytes,
    *,
    media_type: str | None = None,
    filename: str | None = None,
) -> LibraryTitle:
    title = require_library_title(session, normalize_slug(slug))
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


def clear_title_image(session: Session, slug: str) -> LibraryTitle:
    title = require_library_title(session, normalize_slug(slug))
    title.image_bytes = None
    title.image_media_type = None
    title.image_url = None
    session.add(title)
    session.commit()
    session.refresh(title)
    return title


def get_title_image(session: Session, slug: str) -> tuple[bytes, str]:
    title = require_library_title(session, normalize_slug(slug))
    if not title.image_bytes or not title.image_media_type:
        raise NotFoundError("library_title_image", slug)
    return title.image_bytes, title.image_media_type


def title_image_href(title: LibraryTitle) -> str | None:
    if title.image_bytes:
        return f"/library/titles/{title.slug}/image"
    return title.image_url


def title_topics(session: Session, title: LibraryTitle) -> list[LibraryTopic]:
    if title.id is None:
        return []
    topic_ids = [
        link.topic_id
        for link in session.exec(
            select(LibraryTitleTopic).where(LibraryTitleTopic.title_id == title.id)
        ).all()
    ]
    if not topic_ids:
        return []
    topics = list(
        session.exec(select(LibraryTopic).where(col(LibraryTopic.id).in_(topic_ids))).all()
    )
    return sorted(topics, key=lambda topic: topic.slug)


def title_view_for(session: Session, title: LibraryTitle) -> LibraryTitleView:
    return _title_view(title, title_topics(session, title))


def library_dashboard(
    session: Session,
    *,
    as_of: date | None = None,
    period: Period = Period.WEEK,
) -> LibraryDashboardMath:
    as_of = resolve_today(as_of)
    return library_dashboard_math(_title_views(session), as_of=as_of, period=period)


def _title_views(session: Session) -> list[LibraryTitleView]:
    titles = list_library_titles(session)
    topics_by_title = _topics_by_title_id(session)
    return [_title_view(title, topics_by_title.get(title.id or 0, [])) for title in titles]


def _title_view(
    title: LibraryTitle,
    topics: list[LibraryTopic],
) -> LibraryTitleView:
    return LibraryTitleView(
        slug=title.slug,
        name=title.name,
        kind=LibraryKind(title.kind),
        status=LibraryStatus(title.status),
        creator=title.creator,
        recommended_by=title.recommended_by,
        started_on=title.started_on,
        finished_on=title.finished_on,
        progress=title.progress,
        note=title.note,
        rating=title.rating,
        link=title.link,
        topics=tuple(LibraryTopicRef(slug=topic.slug, name=topic.name) for topic in topics),
        image=title_image_href(title),
        created_at=title.created_at,
    )


def _topics_by_title_id(session: Session) -> dict[int, list[LibraryTopic]]:
    topics = {topic.id: topic for topic in session.exec(select(LibraryTopic)).all()}
    grouped: dict[int, list[LibraryTopic]] = {}
    for link in session.exec(select(LibraryTitleTopic)).all():
        topic = topics.get(link.topic_id)
        if topic is None:
            continue
        grouped.setdefault(link.title_id, []).append(topic)
    for topic_list in grouped.values():
        topic_list.sort(key=lambda topic: topic.slug)
    return grouped


def _replace_title_topics(session: Session, title: LibraryTitle, slugs: list[str]) -> None:
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
    topics = [_topic_for_tag(session, slug) for slug in unique]
    for topic in topics:
        if topic.archived_at is not None:
            raise ValidationError(f"library_topic {topic.slug!r} is archived")
    existing = list(
        session.exec(select(LibraryTitleTopic).where(LibraryTitleTopic.title_id == title.id)).all()
    )
    for link in existing:
        session.delete(link)
    session.flush()
    for topic in topics:
        session.add(LibraryTitleTopic(title_id=title.id, topic_id=topic.id))


def _topic_for_tag(session: Session, slug: str) -> LibraryTopic:
    topic = session.exec(select(LibraryTopic).where(LibraryTopic.slug == slug)).first()
    if topic is not None:
        return topic
    topic = LibraryTopic(slug=slug, name=display_name(slug))
    session.add(topic)
    session.flush()
    return topic


def _stamp_status_dates(
    title: LibraryTitle,
    status: LibraryStatus,
    today: date,
) -> None:
    title.status = status
    if status is LibraryStatus.IN_PROGRESS and title.started_on is None:
        title.started_on = today
    if status is LibraryStatus.DONE and title.finished_on is None:
        title.finished_on = today


def _set_image_url(title: LibraryTitle, image_url: str | None) -> None:
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


def _validate_rating(rating: object) -> int | None:
    if rating is None:
        return None
    if isinstance(rating, bool) or not isinstance(rating, int):
        raise ValidationError("rating must be an integer or None")
    if not RATING_MIN <= rating <= RATING_MAX:
        raise ValidationError(f"rating must be between {RATING_MIN} and {RATING_MAX}")
    return rating


def _validate_link(link: object) -> str | None:
    if link is None:
        return None
    if not isinstance(link, str):
        raise ValidationError("link must be a string or None")
    cleaned = link.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(("http://", "https://")):
        raise ValidationError("link must be an http or https URL")
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
