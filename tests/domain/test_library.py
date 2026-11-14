from datetime import date

from atlas.domain import (
    LibraryKind,
    LibraryStatus,
    LibraryTitleView,
    LibraryTopicRef,
    Period,
    library_dashboard_math,
)

AS_OF = date(2026, 8, 14)


def _title(
    slug: str,
    *,
    kind: LibraryKind = LibraryKind.FILM,
    status: LibraryStatus = LibraryStatus.QUEUED,
    name: str | None = None,
    finished_on: date | None = None,
    started_on: date | None = None,
    topics: tuple[LibraryTopicRef, ...] = (),
) -> LibraryTitleView:
    return LibraryTitleView(
        slug=slug,
        name=name or slug.replace("-", " ").title(),
        kind=kind,
        status=status,
        started_on=started_on,
        finished_on=finished_on,
        topics=topics,
    )


def test_dashboard_counts_finished_and_started_in_the_clipped_week():
    programming = LibraryTopicRef("programming", "Programming")
    physics = LibraryTopicRef("physics", "Physics")
    titles = [
        _title(
            "interstellar",
            status=LibraryStatus.DONE,
            finished_on=date(2026, 8, 12),
            topics=(physics,),
        ),
        _title(
            "lex-fridman",
            kind=LibraryKind.PODCAST,
            status=LibraryStatus.DONE,
            finished_on=date(2026, 8, 13),
            topics=(programming,),
        ),
        _title(
            "old-film",
            status=LibraryStatus.DONE,
            finished_on=date(2026, 8, 1),
        ),
        _title(
            "the-office",
            kind=LibraryKind.SERIES,
            status=LibraryStatus.IN_PROGRESS,
            started_on=date(2026, 8, 10),
        ),
        _title("queued-book", kind=LibraryKind.BOOK),
        _title("dropped-anime", kind=LibraryKind.ANIME, status=LibraryStatus.DROPPED),
    ]

    dash = library_dashboard_math(titles, as_of=AS_OF, period=Period.WEEK)

    assert dash.range_start == date(2026, 8, 10)
    assert dash.range_end == AS_OF
    assert dash.finished_in_range == 2
    assert dash.started_in_range == 1
    assert dash.queued == 1
    assert dash.in_progress == 1
    assert dash.done == 3
    assert dash.dropped == 1
    assert [row.kind for row in dash.by_kind] == [LibraryKind.FILM, LibraryKind.PODCAST]
    assert dash.by_kind[0].count == 1
    assert dash.by_kind[0].share == 0.5
    assert [row.slug for row in dash.by_topic] == ["physics", "programming"]
    assert [row.slug for row in dash.recently_finished] == [
        "lex-fridman",
        "interstellar",
        "old-film",
    ]
    assert [row.slug for row in dash.library.done] == ["lex-fridman", "interstellar", "old-film"]
    assert dash.library.in_progress[0].slug == "the-office"


def test_empty_library_has_zero_mix_counts():
    dash = library_dashboard_math([], as_of=AS_OF, period=Period.MONTH)
    assert dash.finished_in_range == 0
    assert dash.by_kind == ()
    assert dash.by_topic == ()
    assert dash.recently_finished == ()
    assert dash.library.queued == ()
