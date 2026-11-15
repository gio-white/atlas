"""Screen-time caps judged per period: "Bad apps at most 1h 30m a day" (screen time doc).

A cap is a target on the summed minutes of a period (day, week, or month). Each period is
satisfied or missed; streaks and adherence count periods. Habits used these helpers before the
habits rebuild; they now have their own calculations in `domain/habits.py`.
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from enum import StrEnum

from atlas.domain.buckets import bucket_for, next_bucket, ranges_intersect
from atlas.domain.enums import Comparator
from atlas.domain.models import Bucket, CapSpec, EntryView
from atlas.domain.rollup import rollup


class BucketOutcome(StrEnum):
    SATISFIED = "satisfied"
    MISSED = "missed"


def is_satisfied(value: float | None, comparator: Comparator, target: float) -> bool:
    if value is None:
        return comparator is Comparator.AT_MOST
    match comparator:
        case Comparator.AT_LEAST:
            return value >= target
        case Comparator.AT_MOST:
            return value <= target
        case Comparator.EXACTLY:
            return value == target


def is_scheduled(cap: CapSpec, bucket: Bucket, as_of: date) -> bool:
    active_end = cap.active_to if cap.active_to is not None else date.max
    if not ranges_intersect(bucket.start, bucket.end, cap.active_from, active_end):
        return False
    return bucket.start <= as_of


def bucket_outcome(cap: CapSpec, entries: Sequence[EntryView], bucket: Bucket) -> BucketOutcome:
    value = rollup(
        [entry for entry in entries if bucket.contains(entry.occurred_on)], cap.aggregation
    )
    if is_satisfied(value, cap.comparator, cap.target_value):
        return BucketOutcome.SATISFIED
    return BucketOutcome.MISSED


def scheduled_buckets(cap: CapSpec, as_of: date) -> list[Bucket]:
    if as_of < cap.active_from:
        return []
    buckets: list[Bucket] = []
    current = bucket_for(cap.active_from, cap.period)
    while current.start <= as_of:
        if is_scheduled(cap, current, as_of):
            buckets.append(current)
        current = next_bucket(current)
    return buckets


def current_streak(cap: CapSpec, entries: Sequence[EntryView], as_of: date) -> int:
    streak = 0
    for bucket, outcome in reversed(_outcomes(cap, entries, as_of)):
        if outcome is BucketOutcome.SATISFIED:
            streak += 1
            continue
        if _still_open(cap, bucket, as_of):
            continue
        break
    return streak


def longest_streak(cap: CapSpec, entries: Sequence[EntryView], as_of: date) -> int:
    best = 0
    run = 0
    for bucket, outcome in _outcomes(cap, entries, as_of):
        if outcome is BucketOutcome.SATISFIED:
            run += 1
            best = max(best, run)
        elif not _still_open(cap, bucket, as_of):
            run = 0
    return best


def adherence_counts(
    cap: CapSpec,
    entries: Sequence[EntryView],
    from_date: date,
    to_date: date,
) -> tuple[int, int]:
    """(satisfied, judged) over complete scheduled periods in the range."""
    if from_date > to_date:
        return 0, 0
    satisfied = 0
    judged = 0
    for bucket, outcome in _outcomes(cap, entries, to_date):
        if not bucket.is_complete(to_date):
            continue
        if not ranges_intersect(bucket.start, bucket.end, from_date, to_date):
            continue
        judged += 1
        satisfied += outcome is BucketOutcome.SATISFIED
    return satisfied, judged


def adherence(
    cap: CapSpec,
    entries: Sequence[EntryView],
    from_date: date,
    to_date: date,
) -> float | None:
    satisfied, judged = adherence_counts(cap, entries, from_date, to_date)
    return None if judged == 0 else satisfied / judged


def _still_open(cap: CapSpec, bucket: Bucket, as_of: date) -> bool:
    """A missed period that can still be met: in progress and not a ceiling already crossed."""
    return bucket.is_in_progress(as_of) and cap.comparator is not Comparator.AT_MOST


def _outcomes(
    cap: CapSpec,
    entries: Sequence[EntryView],
    as_of: date,
) -> list[tuple[Bucket, BucketOutcome]]:
    grouped: dict[date | tuple[int, int], list[EntryView]] = defaultdict(list)
    for entry in entries:
        if entry.occurred_on <= as_of:
            grouped[bucket_for(entry.occurred_on, cap.period).key].append(entry)
    return [
        (bucket, bucket_outcome(cap, grouped.get(bucket.key, []), bucket))
        for bucket in scheduled_buckets(cap, as_of)
    ]
