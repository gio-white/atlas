import math
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
from enum import StrEnum

from atlas.domain.buckets import bucket_for, next_bucket, ranges_intersect
from atlas.domain.enums import Comparator, Period
from atlas.domain.models import Bucket, EntryView, HabitSpec
from atlas.domain.rollup import rollup


class BucketOutcome(StrEnum):
    SATISFIED = "satisfied"
    MISSED = "missed"
    EXCUSED = "excused"


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


def is_scheduled(habit: HabitSpec, bucket: Bucket, as_of: date) -> bool:
    active_end = habit.active_to if habit.active_to is not None else date.max
    if not ranges_intersect(bucket.start, bucket.end, habit.active_from, active_end):
        return False
    if bucket.start > as_of:
        return False
    return not (
        habit.period is Period.DAY
        and habit.weekdays is not None
        and bucket.start.isoweekday() not in habit.weekdays
    )


def available_days(habit: HabitSpec, bucket: Bucket) -> tuple[int, int]:
    """(days in the bucket, days in it not covered by a break)."""
    total = (bucket.end - bucket.start).days + 1
    if not habit.breaks:
        return total, total
    covered = sum(
        1 for offset in range(total) if habit.on_break(bucket.start + timedelta(days=offset))
    )
    return total, total - covered


def is_excused(habit: HabitSpec, bucket: Bucket) -> bool:
    return available_days(habit, bucket)[1] == 0


def bucket_target(habit: HabitSpec, bucket: Bucket) -> float | None:
    """The target this bucket is judged against, or None when a break excuses it.

    A break that covers part of a week or month scales an `at_least` target to the
    days still available, rounded up; ceilings and exact targets are left alone.
    """
    total, available = available_days(habit, bucket)
    if available == 0:
        return None
    if available == total or habit.comparator is not Comparator.AT_LEAST:
        return habit.target_value
    return float(math.ceil(habit.target_value * available / total))


def bucket_outcome(
    habit: HabitSpec,
    entries: Sequence[EntryView],
    bucket: Bucket,
) -> BucketOutcome:
    target = bucket_target(habit, bucket)
    if target is None:
        return BucketOutcome.EXCUSED
    value = rollup(
        [entry for entry in entries if bucket.contains(entry.occurred_on)], habit.aggregation
    )
    if is_satisfied(value, habit.comparator, target):
        return BucketOutcome.SATISFIED
    return BucketOutcome.MISSED


def scheduled_buckets(habit: HabitSpec, as_of: date) -> list[Bucket]:
    if as_of < habit.active_from:
        return []
    buckets: list[Bucket] = []
    current = bucket_for(habit.active_from, habit.period)
    while current.start <= as_of:
        if is_scheduled(habit, current, as_of):
            buckets.append(current)
        current = next_bucket(current)
    return buckets


def current_streak(habit: HabitSpec, entries: Sequence[EntryView], as_of: date) -> int:
    outcomes = _outcomes(habit, entries, as_of)
    streak = 0
    for index in range(len(outcomes) - 1, -1, -1):
        bucket, outcome = outcomes[index]
        if outcome is BucketOutcome.EXCUSED:
            continue
        if outcome is BucketOutcome.SATISFIED:
            streak += 1
            continue
        if _still_open(habit, bucket, as_of):
            continue
        break
    return streak


def longest_streak(habit: HabitSpec, entries: Sequence[EntryView], as_of: date) -> int:
    best = 0
    run = 0
    for bucket, outcome in _outcomes(habit, entries, as_of):
        if outcome is BucketOutcome.EXCUSED:
            continue
        if outcome is BucketOutcome.SATISFIED:
            run += 1
            best = max(best, run)
        elif not _still_open(habit, bucket, as_of):
            run = 0
    return best


def adherence_counts(
    habit: HabitSpec,
    entries: Sequence[EntryView],
    from_date: date,
    to_date: date,
) -> tuple[int, int]:
    """(satisfied, judged) over complete, non-excused scheduled buckets in the range."""
    if from_date > to_date:
        return 0, 0
    satisfied = 0
    judged = 0
    for bucket, outcome in _outcomes(habit, entries, to_date):
        if not bucket.is_complete(to_date) or outcome is BucketOutcome.EXCUSED:
            continue
        if not ranges_intersect(bucket.start, bucket.end, from_date, to_date):
            continue
        judged += 1
        satisfied += outcome is BucketOutcome.SATISFIED
    return satisfied, judged


def adherence(
    habit: HabitSpec,
    entries: Sequence[EntryView],
    from_date: date,
    to_date: date,
) -> float | None:
    satisfied, judged = adherence_counts(habit, entries, from_date, to_date)
    return None if judged == 0 else satisfied / judged


def _still_open(habit: HabitSpec, bucket: Bucket, as_of: date) -> bool:
    """A missed bucket that can still be met: in progress and not a ceiling already crossed."""
    return bucket.is_in_progress(as_of) and habit.comparator is not Comparator.AT_MOST


def _outcomes(
    habit: HabitSpec,
    entries: Sequence[EntryView],
    as_of: date,
) -> list[tuple[Bucket, BucketOutcome]]:
    grouped = _group_by_bucket(
        [entry for entry in entries if entry.occurred_on <= as_of], habit.period
    )
    return [
        (bucket, bucket_outcome(habit, grouped.get(bucket.key, []), bucket))
        for bucket in scheduled_buckets(habit, as_of)
    ]


def _group_by_bucket(
    entries: Sequence[EntryView],
    period: Period,
) -> dict[date | tuple[int, int], list[EntryView]]:
    grouped: dict[date | tuple[int, int], list[EntryView]] = defaultdict(list)
    for entry in entries:
        grouped[bucket_for(entry.occurred_on, period).key].append(entry)
    return grouped
