from datetime import date

import pytest
from sqlmodel import select

from atlas.db.models import Entry
from atlas.domain import EntertainmentKind, EntertainmentStatus, Period
from atlas.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    create_entertainment_title,
    create_entertainment_topic,
    entertainment_dashboard,
    entertainment_view,
    export_all,
    get_title_image,
    list_entertainment_titles,
    set_title_image,
    update_entertainment_title,
)

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _topic(session, slug: str = "physics"):
    return create_entertainment_topic(session, slug)


def test_create_title_does_not_write_an_entry(session):
    _topic(session)
    title = create_entertainment_title(
        session,
        "interstellar",
        kind=EntertainmentKind.FILM,
        name="Interstellar",
        creator="Christopher Nolan",
        topics=["physics"],
        status=EntertainmentStatus.DONE,
        finished_on=date(2026, 8, 12),
    )
    assert title.status is EntertainmentStatus.DONE
    assert session.exec(select(Entry)).all() == []
    listed = list_entertainment_titles(session, topic="physics")
    assert [row.slug for row in listed] == ["interstellar"]


def test_duplicate_topic_slug_is_rejected(session):
    _topic(session, "math")
    with pytest.raises(AlreadyExistsError):
        create_entertainment_topic(session, "math")


def test_marking_done_stamps_finished_on(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    create_entertainment_title(session, "queued-book", kind=EntertainmentKind.BOOK)
    updated = update_entertainment_title(session, "queued-book", status=EntertainmentStatus.DONE)
    assert updated.status is EntertainmentStatus.DONE
    assert updated.finished_on is not None


def test_image_url_and_upload_are_exclusive(session):
    create_entertainment_title(
        session,
        "poster",
        kind=EntertainmentKind.FILM,
        image_url="https://example.com/poster.jpg",
    )
    updated = set_title_image(session, "poster", PNG, media_type="image/png")
    assert updated.image_url is None
    data, media_type = get_title_image(session, "poster")
    assert data == PNG
    assert media_type == "image/png"
    cleared = update_entertainment_title(
        session, "poster", image_url="https://example.com/other.jpg"
    )
    assert cleared.image_bytes is None
    assert cleared.image_url == "https://example.com/other.jpg"
    with pytest.raises(NotFoundError):
        get_title_image(session, "poster")


def test_image_rejects_large_and_unknown_types(session):
    create_entertainment_title(session, "clip", kind=EntertainmentKind.VIDEO)
    with pytest.raises(ValidationError, match="jpeg"):
        set_title_image(session, "clip", b"not-an-image", media_type="application/pdf")
    with pytest.raises(ValidationError, match="2 MiB"):
        set_title_image(session, "clip", b"x" * (2 * 1024 * 1024 + 1), media_type="image/png")


def test_dashboard_and_view_count_library_status(session):
    _topic(session, "programming")
    create_entertainment_title(
        session,
        "lex",
        kind=EntertainmentKind.PODCAST,
        status=EntertainmentStatus.DONE,
        finished_on=date(2026, 8, 13),
        topics=["programming"],
    )
    create_entertainment_title(
        session,
        "office",
        kind=EntertainmentKind.SERIES,
        status=EntertainmentStatus.IN_PROGRESS,
        started_on=date(2026, 8, 10),
    )
    dash = entertainment_dashboard(session, as_of=date(2026, 8, 14), period=Period.WEEK)
    assert dash.finished_in_range == 1
    assert dash.in_progress == 1
    assert dash.library.done[0].slug == "lex"
    assert dash.library.done[0].topics[0].slug == "programming"
    view = entertainment_view(session, as_of=date(2026, 8, 14))
    assert view.finished_this_week == 1
    assert view.in_progress == 1
    assert view.last_finished is not None
    assert view.last_finished.slug == "lex"


def test_export_includes_entertainment_without_entries(session):
    _topic(session, "finance")
    create_entertainment_title(
        session,
        "atomic-habits",
        kind=EntertainmentKind.BOOK,
        topics=["finance"],
        image_url="https://example.com/atomic.jpg",
    )
    payload = export_all(session)
    assert payload["entertainment_topics"][0]["slug"] == "finance"
    assert payload["entertainment_titles"][0]["slug"] == "atomic-habits"
    assert payload["entertainment_titles"][0]["topics"] == ["finance"]
    assert payload["entries"] == []
