from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from atlas.domain.enums import LibraryKind, LibraryStatus, Period
from atlas.domain.models import LibraryTitleView, LibraryTopicRef
from atlas.domain.screen import clipped_period_range

RECENTLY_FINISHED_LIMIT = 8
LIBRARY_STATUSES = (
    LibraryStatus.QUEUED,
    LibraryStatus.IN_PROGRESS,
    LibraryStatus.DONE,
    LibraryStatus.DROPPED,
)


@dataclass(frozen=True, slots=True)
class LibraryKindCount:
    kind: LibraryKind
    count: int
    share: float


@dataclass(frozen=True, slots=True)
class LibraryTopicCount:
    slug: str
    name: str
    count: int
    share: float


@dataclass(frozen=True, slots=True)
class LibraryShelves:
    queued: tuple[LibraryTitleView, ...]
    in_progress: tuple[LibraryTitleView, ...]
    done: tuple[LibraryTitleView, ...]
    dropped: tuple[LibraryTitleView, ...]


@dataclass(frozen=True, slots=True)
class LibraryDashboardMath:
    period: Period
    as_of: date
    range_start: date
    range_end: date
    finished_in_range: int
    started_in_range: int
    queued: int
    in_progress: int
    done: int
    dropped: int
    by_kind: tuple[LibraryKindCount, ...]
    by_topic: tuple[LibraryTopicCount, ...]
    recently_finished: tuple[LibraryTitleView, ...]
    library: LibraryShelves


def library_dashboard_math(
    titles: Sequence[LibraryTitleView],
    *,
    as_of: date,
    period: Period,
) -> LibraryDashboardMath:
    period = Period(period)
    range_start, range_end = clipped_period_range(as_of, period)
    finished_in = [
        title
        for title in titles
        if title.finished_on is not None and range_start <= title.finished_on <= range_end
    ]
    started_in = [
        title
        for title in titles
        if title.started_on is not None and range_start <= title.started_on <= range_end
    ]
    grouped = _library(titles)
    return LibraryDashboardMath(
        period=period,
        as_of=as_of,
        range_start=range_start,
        range_end=range_end,
        finished_in_range=len(finished_in),
        started_in_range=len(started_in),
        queued=len(grouped.queued),
        in_progress=len(grouped.in_progress),
        done=len(grouped.done),
        dropped=len(grouped.dropped),
        by_kind=_kind_counts(finished_in),
        by_topic=_topic_counts(finished_in),
        recently_finished=_recently_finished(titles, as_of),
        library=grouped,
    )


def _library(titles: Sequence[LibraryTitleView]) -> LibraryShelves:
    buckets: dict[LibraryStatus, list[LibraryTitleView]] = {
        status: [] for status in LIBRARY_STATUSES
    }
    for title in titles:
        buckets[title.status].append(title)
    return LibraryShelves(
        queued=_sorted_column(buckets[LibraryStatus.QUEUED], LibraryStatus.QUEUED),
        in_progress=_sorted_column(buckets[LibraryStatus.IN_PROGRESS], LibraryStatus.IN_PROGRESS),
        done=_sorted_column(buckets[LibraryStatus.DONE], LibraryStatus.DONE),
        dropped=_sorted_column(buckets[LibraryStatus.DROPPED], LibraryStatus.DROPPED),
    )


def _sorted_column(
    titles: Sequence[LibraryTitleView],
    status: LibraryStatus,
) -> tuple[LibraryTitleView, ...]:
    if status is LibraryStatus.DONE:
        return tuple(
            sorted(
                titles,
                key=lambda title: (-_ordinal(title.finished_on), title.name.lower()),
            )
        )
    if status is LibraryStatus.IN_PROGRESS:
        return tuple(
            sorted(
                titles,
                key=lambda title: (-_ordinal(title.started_on), title.name.lower()),
            )
        )
    return tuple(sorted(titles, key=lambda title: title.name.lower()))


def _recently_finished(
    titles: Sequence[LibraryTitleView],
    as_of: date,
    *,
    limit: int = RECENTLY_FINISHED_LIMIT,
) -> tuple[LibraryTitleView, ...]:
    finished = [
        title for title in titles if title.finished_on is not None and title.finished_on <= as_of
    ]
    ordered = sorted(
        finished,
        key=lambda title: (-_ordinal(title.finished_on), title.name.lower()),
    )
    return tuple(ordered[:limit])


def _kind_counts(titles: Sequence[LibraryTitleView]) -> tuple[LibraryKindCount, ...]:
    total = len(titles)
    if total == 0:
        return ()
    counts: dict[LibraryKind, int] = {}
    for title in titles:
        counts[title.kind] = counts.get(title.kind, 0) + 1
    return tuple(
        LibraryKindCount(kind=kind, count=count, share=count / total)
        for kind, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].value))
    )


def _topic_counts(titles: Sequence[LibraryTitleView]) -> tuple[LibraryTopicCount, ...]:
    if not titles:
        return ()
    counts: dict[str, tuple[LibraryTopicRef, int]] = {}
    for title in titles:
        seen: set[str] = set()
        for topic in title.topics:
            if topic.slug in seen:
                continue
            seen.add(topic.slug)
            current = counts.get(topic.slug)
            counts[topic.slug] = (topic, 1 if current is None else current[1] + 1)
    total = len(titles)
    return tuple(
        LibraryTopicCount(slug=topic.slug, name=topic.name, count=count, share=count / total)
        for topic, count in sorted(counts.values(), key=lambda item: (-item[1], item[0].slug))
    )


def _ordinal(value: date | None) -> int:
    return 0 if value is None else value.toordinal()
