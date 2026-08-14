from datetime import date

from atlas.domain import (
    EntertainmentKind,
    EntertainmentStatus,
    EntertainmentTitleView,
    EntertainmentTopicRef,
    Period,
    entertainment_dashboard_math,
    finished_in_week,
    last_finished,
)

AS_OF = date(2026, 8, 14)


def _title(
    slug: str,
    *,
    kind: EntertainmentKind = EntertainmentKind.FILM,
    status: EntertainmentStatus = EntertainmentStatus.QUEUED,
    name: str | None = None,
    finished_on: date | None = None,
    started_on: date | None = None,
    topics: tuple[EntertainmentTopicRef, ...] = (),
) -> EntertainmentTitleView:
    return EntertainmentTitleView(
        slug=slug,
        name=name or slug.replace("-", " ").title(),
        kind=kind,
        status=status,
        started_on=started_on,
        finished_on=finished_on,
        topics=topics,
    )


def test_dashboard_counts_finished_and_started_in_the_clipped_week():
    programming = EntertainmentTopicRef("programming", "Programming")
    physics = EntertainmentTopicRef("physics", "Physics")
    titles = [
        _title(
            "interstellar",
            status=EntertainmentStatus.DONE,
            finished_on=date(2026, 8, 12),
            topics=(physics,),
        ),
        _title(
            "lex-fridman",
            kind=EntertainmentKind.PODCAST,
            status=EntertainmentStatus.DONE,
            finished_on=date(2026, 8, 13),
            topics=(programming,),
        ),
        _title(
            "old-film",
            status=EntertainmentStatus.DONE,
            finished_on=date(2026, 8, 1),
        ),
        _title(
            "the-office",
            kind=EntertainmentKind.SERIES,
            status=EntertainmentStatus.IN_PROGRESS,
            started_on=date(2026, 8, 10),
        ),
        _title("queued-book", kind=EntertainmentKind.BOOK),
        _title("dropped-anime", kind=EntertainmentKind.ANIME, status=EntertainmentStatus.DROPPED),
    ]

    dash = entertainment_dashboard_math(titles, as_of=AS_OF, period=Period.WEEK)

    assert dash.range_start == date(2026, 8, 10)
    assert dash.range_end == AS_OF
    assert dash.finished_in_range == 2
    assert dash.started_in_range == 1
    assert dash.queued == 1
    assert dash.in_progress == 1
    assert dash.done == 3
    assert dash.dropped == 1
    assert [row.kind for row in dash.by_kind] == [EntertainmentKind.FILM, EntertainmentKind.PODCAST]
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


def test_finished_in_week_and_last_finished_ignore_the_future():
    titles = [
        _title("today", status=EntertainmentStatus.DONE, finished_on=AS_OF),
        _title("tomorrow", status=EntertainmentStatus.DONE, finished_on=date(2026, 8, 15)),
        _title("last-week", status=EntertainmentStatus.DONE, finished_on=date(2026, 8, 9)),
    ]

    assert finished_in_week(titles, as_of=AS_OF) == 1
    assert last_finished(titles, as_of=AS_OF).slug == "today"


def test_empty_library_has_zero_mix_counts():
    dash = entertainment_dashboard_math([], as_of=AS_OF, period=Period.MONTH)
    assert dash.finished_in_range == 0
    assert dash.by_kind == ()
    assert dash.by_topic == ()
    assert dash.recently_finished == ()
    assert dash.library.queued == ()
