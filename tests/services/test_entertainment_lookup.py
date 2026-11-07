import json

import pytest

from atlas.domain import EntertainmentKind, EntertainmentStatus
from atlas.services import (
    AlreadyExistsError,
    UpstreamError,
    ValidationError,
    create_entertainment_title,
    create_title_from_link,
    lookup_link,
)

VIDEO = "https://www.youtube.com/watch?v=aircAruvnKk"


def fake_fetch(pages: dict[str, str]):
    calls: list[str] = []

    def fetch(url: str) -> str:
        calls.append(url)
        for prefix, body in pages.items():
            if url.startswith(prefix):
                return body
        raise UpstreamError(f"no page for {url}")

    fetch.calls = calls
    return fetch


YOUTUBE = fake_fetch(
    {
        "https://www.youtube.com/oembed": json.dumps(
            {
                "title": "But what is a neural network?",
                "author_name": "3Blue1Brown",
                "thumbnail_url": "https://i.ytimg.com/vi/aircAruvnKk/hqdefault.jpg",
            }
        )
    }
)


def test_lookup_uses_oembed_without_fetching_the_page(session):
    result = lookup_link(session, VIDEO, fetch=YOUTUBE)
    assert result.suggestion.name == "But what is a neural network?"
    assert result.suggestion.kind is EntertainmentKind.VIDEO
    assert result.existing is None
    assert all("oembed" in call for call in YOUTUBE.calls)


def test_lookup_falls_back_to_page_meta_and_flags_saved_links(session):
    page = '<title>Arrival (2016)</title><meta property="og:type" content="video.movie">'
    fetch = fake_fetch({"https://example.com/": page})
    result = lookup_link(session, "https://example.com/arrival", fetch=fetch)
    assert result.suggestion.name == "Arrival (2016)"
    assert result.suggestion.kind is EntertainmentKind.FILM

    create_entertainment_title(
        session, "arrival", kind=EntertainmentKind.FILM, link="https://example.com/arrival"
    )
    assert lookup_link(session, "https://example.com/arrival", fetch=fetch).existing == "arrival"


def test_lookup_errors(session):
    with pytest.raises(ValidationError):
        lookup_link(session, "not a link", fetch=fake_fetch({}))
    with pytest.raises(UpstreamError):
        lookup_link(session, "https://unreachable.example/", fetch=fake_fetch({}))


def test_create_from_link_fills_fields_and_refuses_duplicates(session):
    title = create_title_from_link(
        session,
        VIDEO,
        status=EntertainmentStatus.DONE,
        topics=["math"],
        fetch=YOUTUBE,
    )
    assert title.slug == "but-what-is-a-neural-network"
    assert title.creator == "3Blue1Brown"
    assert title.link == VIDEO
    assert title.image_url == "https://i.ytimg.com/vi/aircAruvnKk/hqdefault.jpg"
    assert title.finished_on is not None
    with pytest.raises(AlreadyExistsError):
        create_title_from_link(session, VIDEO, fetch=YOUTUBE)

    other = create_title_from_link(
        session, f"{VIDEO}&t=10", kind=EntertainmentKind.OTHER, fetch=YOUTUBE
    )
    assert other.slug == "but-what-is-a-neural-network-other"
    assert other.kind is EntertainmentKind.OTHER


def test_create_from_link_needs_a_name(session):
    fetch = fake_fetch({"https://example.com/": "<p>no metadata</p>"})
    with pytest.raises(ValidationError):
        create_title_from_link(session, "https://example.com/blank", fetch=fetch)
