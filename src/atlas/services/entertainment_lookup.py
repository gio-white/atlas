import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from sqlmodel import Session, select

from atlas.db.models import EntertainmentTitle
from atlas.domain import (
    EntertainmentKind,
    EntertainmentStatus,
    LinkSuggestion,
    oembed_url,
    parse_page_meta,
    suggest_from_sources,
)
from atlas.domain.entertainment_link import host_of
from atlas.services.entertainment import create_entertainment_title
from atlas.services.errors import AlreadyExistsError, UpstreamError, ValidationError

FETCH_TIMEOUT_SECONDS = 8
FETCH_MAX_BYTES = 2 * 1024 * 1024
_USER_AGENT = "Mozilla/5.0 (compatible; Atlas/0.1; personal library link preview)"
_SLUG_CHUNK = re.compile(r"[^a-z0-9]+")
_OEMBED_FIELDS = ("title", "author_name", "thumbnail_url")

Fetch = Callable[[str], str]
"""Returns the decoded body at a URL, or raises `UpstreamError`."""


@dataclass(frozen=True, slots=True)
class LinkLookup:
    suggestion: LinkSuggestion
    existing: str | None


def http_get_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
            "Accept-Language": "en",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            body = response.read(FETCH_MAX_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise UpstreamError(f"{host_of(url)} answered {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        raise UpstreamError(f"could not reach {host_of(url)}: {reason}") from exc
    return body.decode(charset, errors="replace")


def lookup_link(session: Session, url: str, *, fetch: Fetch | None = None) -> LinkLookup:
    """Suggest name, kind, creator, and poster for a link, and say if it is already saved."""
    link = _require_link(url)
    fetch = fetch or http_get_text
    oembed = _fetch_oembed(link, fetch)
    meta: dict[str, str] | None = None
    if oembed is None or not all(oembed.get(key) for key in _OEMBED_FIELDS):
        try:
            meta = parse_page_meta(fetch(link))
        except UpstreamError:
            if oembed is None:
                raise
    suggestion = suggest_from_sources(link, oembed=oembed, meta=meta)
    existing = session.exec(
        select(EntertainmentTitle).where(EntertainmentTitle.link == link)
    ).first()
    return LinkLookup(suggestion=suggestion, existing=existing.slug if existing else None)


def create_title_from_link(
    session: Session,
    url: str,
    *,
    kind: EntertainmentKind | None = None,
    status: EntertainmentStatus = EntertainmentStatus.QUEUED,
    topics: list[str] | None = None,
    note: str | None = None,
    fetch: Fetch | None = None,
) -> EntertainmentTitle:
    """Look a link up and save it in one step; refuses links already in the library."""
    lookup = lookup_link(session, url, fetch=fetch)
    if lookup.existing is not None:
        raise AlreadyExistsError("entertainment_title", lookup.existing)
    suggestion = lookup.suggestion
    if suggestion.name is None:
        raise ValidationError("could not find a title at that link; add it by hand")
    resolved_kind = EntertainmentKind(kind or suggestion.kind or EntertainmentKind.OTHER)
    return create_entertainment_title(
        session,
        unique_title_slug(session, suggestion.name, resolved_kind),
        kind=resolved_kind,
        name=suggestion.name,
        creator=suggestion.creator,
        status=status,
        note=note,
        link=suggestion.link,
        topics=topics,
        image_url=suggestion.image_url,
    )


def unique_title_slug(session: Session, name: str, kind: EntertainmentKind) -> str:
    base = _SLUG_CHUNK.sub("-", name.lower()).strip("-")[:60].strip("-") or str(kind)
    taken = set(session.exec(select(EntertainmentTitle.slug)).all())
    if base not in taken:
        return base
    with_kind = f"{base}-{kind}"
    if with_kind not in taken:
        return with_kind
    index = 2
    while f"{with_kind}-{index}" in taken:
        index += 1
    return f"{with_kind}-{index}"


def _fetch_oembed(link: str, fetch: Fetch) -> dict[str, object] | None:
    endpoint = oembed_url(link)
    if endpoint is None:
        return None
    try:
        payload = json.loads(fetch(endpoint))
    except (UpstreamError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _require_link(url: str) -> str:
    cleaned = url.strip() if isinstance(url, str) else ""
    if not cleaned.startswith(("http://", "https://")) or not host_of(cleaned):
        raise ValidationError("link must be an http or https URL")
    return cleaned
