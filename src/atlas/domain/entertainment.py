from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from atlas.domain.buckets import bucket_for
from atlas.domain.enums import EntertainmentKind, EntertainmentStatus, Period
from atlas.domain.models import EntertainmentTitleView, EntertainmentTopicRef
from atlas.domain.screen import clipped_period_range

RECENTLY_FINISHED_LIMIT = 8
LIBRARY_STATUSES = (
    EntertainmentStatus.QUEUED,
    EntertainmentStatus.IN_PROGRESS,
    EntertainmentStatus.DONE,
    EntertainmentStatus.DROPPED,
)


@dataclass(frozen=True, slots=True)
class EntertainmentKindCount:
    kind: EntertainmentKind
    count: int
    share: float


@dataclass(frozen=True, slots=True)
class EntertainmentTopicCount:
    slug: str
    name: str
    count: int
    share: float


@dataclass(frozen=True, slots=True)
class EntertainmentLibrary:
    queued: tuple[EntertainmentTitleView, ...]
    in_progress: tuple[EntertainmentTitleView, ...]
    done: tuple[EntertainmentTitleView, ...]
    dropped: tuple[EntertainmentTitleView, ...]


@dataclass(frozen=True, slots=True)
class EntertainmentDashboardMath:
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
    by_kind: tuple[EntertainmentKindCount, ...]
    by_topic: tuple[EntertainmentTopicCount, ...]
    recently_finished: tuple[EntertainmentTitleView, ...]
    library: EntertainmentLibrary


def entertainment_dashboard_math(
    titles: Sequence[EntertainmentTitleView],
    *,
    as_of: date,
    period: Period,
) -> EntertainmentDashboardMath:
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
    return EntertainmentDashboardMath(
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


def finished_in_week(
    titles: Sequence[EntertainmentTitleView],
    *,
    as_of: date,
) -> int:
    week = bucket_for(as_of, Period.WEEK)
    end = min(week.end, as_of)
    return sum(
        1
        for title in titles
        if title.finished_on is not None and week.start <= title.finished_on <= end
    )


def last_finished(
    titles: Sequence[EntertainmentTitleView],
    *,
    as_of: date,
) -> EntertainmentTitleView | None:
    recent = _recently_finished(titles, as_of, limit=1)
    return recent[0] if recent else None


def _library(titles: Sequence[EntertainmentTitleView]) -> EntertainmentLibrary:
    buckets: dict[EntertainmentStatus, list[EntertainmentTitleView]] = {
        status: [] for status in LIBRARY_STATUSES
    }
    for title in titles:
        buckets[title.status].append(title)
    return EntertainmentLibrary(
        queued=_sorted_column(buckets[EntertainmentStatus.QUEUED], EntertainmentStatus.QUEUED),
        in_progress=_sorted_column(
            buckets[EntertainmentStatus.IN_PROGRESS], EntertainmentStatus.IN_PROGRESS
        ),
        done=_sorted_column(buckets[EntertainmentStatus.DONE], EntertainmentStatus.DONE),
        dropped=_sorted_column(buckets[EntertainmentStatus.DROPPED], EntertainmentStatus.DROPPED),
    )


def _sorted_column(
    titles: Sequence[EntertainmentTitleView],
    status: EntertainmentStatus,
) -> tuple[EntertainmentTitleView, ...]:
    if status is EntertainmentStatus.DONE:
        return tuple(
            sorted(
                titles,
                key=lambda title: (-_ordinal(title.finished_on), title.name.lower()),
            )
        )
    if status is EntertainmentStatus.IN_PROGRESS:
        return tuple(
            sorted(
                titles,
                key=lambda title: (-_ordinal(title.started_on), title.name.lower()),
            )
        )
    return tuple(sorted(titles, key=lambda title: title.name.lower()))


def _recently_finished(
    titles: Sequence[EntertainmentTitleView],
    as_of: date,
    *,
    limit: int = RECENTLY_FINISHED_LIMIT,
) -> tuple[EntertainmentTitleView, ...]:
    finished = [
        title for title in titles if title.finished_on is not None and title.finished_on <= as_of
    ]
    ordered = sorted(
        finished,
        key=lambda title: (-_ordinal(title.finished_on), title.name.lower()),
    )
    return tuple(ordered[:limit])


def _kind_counts(titles: Sequence[EntertainmentTitleView]) -> tuple[EntertainmentKindCount, ...]:
    total = len(titles)
    if total == 0:
        return ()
    counts: dict[EntertainmentKind, int] = {}
    for title in titles:
        counts[title.kind] = counts.get(title.kind, 0) + 1
    return tuple(
        EntertainmentKindCount(kind=kind, count=count, share=count / total)
        for kind, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].value))
    )


def _topic_counts(titles: Sequence[EntertainmentTitleView]) -> tuple[EntertainmentTopicCount, ...]:
    if not titles:
        return ()
    counts: dict[str, tuple[EntertainmentTopicRef, int]] = {}
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
        EntertainmentTopicCount(slug=topic.slug, name=topic.name, count=count, share=count / total)
        for topic, count in sorted(counts.values(), key=lambda item: (-item[1], item[0].slug))
    )


def _ordinal(value: date | None) -> int:
    return 0 if value is None else value.toordinal()
