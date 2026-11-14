from datetime import date

import pytest
from sqlmodel import select

from atlas.db.models import Entry
from atlas.domain import LibraryKind, LibraryStatus, Period
from atlas.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    create_library_title,
    create_library_topic,
    delete_library_title,
    export_all,
    get_library_title,
    get_library_topic,
    get_title_image,
    import_all,
    library_dashboard,
    list_library_titles,
    set_title_image,
    update_library_title,
)

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _topic(session, slug: str = "physics"):
    return create_library_topic(session, slug)


def test_create_title_does_not_write_an_entry(session):
    _topic(session)
    title = create_library_title(
        session,
        "interstellar",
        kind=LibraryKind.FILM,
        name="Interstellar",
        creator="Christopher Nolan",
        topics=["physics"],
        status=LibraryStatus.DONE,
        finished_on=date(2026, 8, 12),
    )
    assert title.status is LibraryStatus.DONE
    assert session.exec(select(Entry)).all() == []
    listed = list_library_titles(session, topic="physics")
    assert [row.slug for row in listed] == ["interstellar"]


def test_duplicate_topic_slug_is_rejected(session):
    _topic(session, "math")
    with pytest.raises(AlreadyExistsError):
        create_library_topic(session, "math")


def test_marking_done_stamps_finished_on(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    create_library_title(session, "queued-book", kind=LibraryKind.BOOK)
    updated = update_library_title(session, "queued-book", status=LibraryStatus.DONE)
    assert updated.status is LibraryStatus.DONE
    assert updated.finished_on is not None


def test_image_url_and_upload_are_exclusive(session):
    create_library_title(
        session,
        "poster",
        kind=LibraryKind.FILM,
        image_url="https://example.com/poster.jpg",
    )
    updated = set_title_image(session, "poster", PNG, media_type="image/png")
    assert updated.image_url is None
    data, media_type = get_title_image(session, "poster")
    assert data == PNG
    assert media_type == "image/png"
    cleared = update_library_title(session, "poster", image_url="https://example.com/other.jpg")
    assert cleared.image_bytes is None
    assert cleared.image_url == "https://example.com/other.jpg"
    with pytest.raises(NotFoundError):
        get_title_image(session, "poster")


def test_image_rejects_large_and_unknown_types(session):
    create_library_title(session, "clip", kind=LibraryKind.VIDEO)
    with pytest.raises(ValidationError, match="jpeg"):
        set_title_image(session, "clip", b"not-an-image", media_type="application/pdf")
    with pytest.raises(ValidationError, match="2 MiB"):
        set_title_image(session, "clip", b"x" * (2 * 1024 * 1024 + 1), media_type="image/png")


def test_dashboard_and_view_count_library_status(session):
    _topic(session, "programming")
    create_library_title(
        session,
        "lex",
        kind=LibraryKind.PODCAST,
        status=LibraryStatus.DONE,
        finished_on=date(2026, 8, 13),
        topics=["programming"],
    )
    create_library_title(
        session,
        "office",
        kind=LibraryKind.SERIES,
        status=LibraryStatus.IN_PROGRESS,
        started_on=date(2026, 8, 10),
    )
    dash = library_dashboard(session, as_of=date(2026, 8, 14), period=Period.WEEK)
    assert dash.finished_in_range == 1
    assert dash.in_progress == 1
    assert dash.library.done[0].slug == "lex"
    assert dash.library.done[0].topics[0].slug == "programming"


def test_export_includes_library_without_entries(session):
    _topic(session, "finance")
    create_library_title(
        session,
        "atomic-habits",
        kind=LibraryKind.BOOK,
        topics=["finance"],
        image_url="https://example.com/atomic.jpg",
    )
    payload = export_all(session)
    assert payload["library_topics"][0]["slug"] == "finance"
    assert payload["library_titles"][0]["slug"] == "atomic-habits"
    assert payload["library_titles"][0]["topics"] == ["finance"]
    assert payload["entries"] == []


def test_rating_and_link_are_validated_and_clearable(session):
    title = create_library_title(
        session,
        "kind-of-blue",
        kind=LibraryKind.MUSIC,
        rating=5,
        link=" https://open.spotify.com/album/kind-of-blue ",
    )
    assert title.rating == 5
    assert title.link == "https://open.spotify.com/album/kind-of-blue"

    for bad in (0, 6, True):
        with pytest.raises(ValidationError):
            update_library_title(session, "kind-of-blue", rating=bad)
    with pytest.raises(ValidationError):
        update_library_title(session, "kind-of-blue", link="spotify:album:1")

    cleared = update_library_title(session, "kind-of-blue", rating=None, link="")
    assert cleared.rating is None
    assert cleared.link is None


def test_unknown_tags_are_created_on_the_fly(session):
    title = create_library_title(
        session, "huberman", kind=LibraryKind.PODCAST, topics=["sleep-science"]
    )
    topic = get_library_topic(session, "sleep-science")
    assert topic.name == "Sleep Science"
    listed = list_library_titles(session, topic="sleep-science")
    assert [row.slug for row in listed] == [title.slug]


def test_delete_title_removes_it_and_its_tag_links(session):
    _topic(session)
    create_library_title(session, "cosmos", kind=LibraryKind.SERIES, topics=["physics"])
    delete_library_title(session, "cosmos")
    with pytest.raises(NotFoundError):
        get_library_title(session, "cosmos")
    assert export_all(session)["library_titles"] == []
    assert list_library_titles(session, topic="physics") == []
    create_library_title(session, "cosmos", kind=LibraryKind.SERIES)


def test_rating_and_link_survive_export_and_import(session):
    create_library_title(
        session,
        "dune",
        kind=LibraryKind.BOOK,
        rating=4,
        link="https://openlibrary.org/works/OL893415W",
    )
    payload = export_all(session)
    row = payload["library_titles"][0]
    assert row["rating"] == 4
    assert row["link"] == "https://openlibrary.org/works/OL893415W"
    delete_library_title(session, "dune")
    import_all(session, payload)
    restored = get_library_title(session, "dune")
    assert restored.rating == 4
    assert restored.link == "https://openlibrary.org/works/OL893415W"
