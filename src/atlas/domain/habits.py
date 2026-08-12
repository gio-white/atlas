from collections import defaultdict
from collections.abc import Sequence
from datetime import date

from atlas.domain.buckets import bucket_for, next_bucket, ranges_intersect
from atlas.domain.enums import Comparator, Period
from atlas.domain.models import Bucket, EntryView, HabitSpec
from atlas.domain.rollup import rollup


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
    buckets = scheduled_buckets(habit, as_of)
    if not buckets:
        return 0
    grouped = _group_by_bucket(_up_to(entries, as_of), habit.period)
    index = len(buckets) - 1
    streak = 0
    last = buckets[index]
    if last.is_in_progress(as_of):
        if _bucket_satisfied(habit, grouped, last):
            streak += 1
        index -= 1
    while index >= 0:
        if not _bucket_satisfied(habit, grouped, buckets[index]):
            break
        streak += 1
        index -= 1
    return streak


def longest_streak(habit: HabitSpec, entries: Sequence[EntryView], as_of: date) -> int:
    buckets = scheduled_buckets(habit, as_of)
    grouped = _group_by_bucket(_up_to(entries, as_of), habit.period)
    best = 0
    run = 0
    for bucket in buckets:
        if bucket.is_in_progress(as_of) and not _bucket_satisfied(habit, grouped, bucket):
            continue
        if _bucket_satisfied(habit, grouped, bucket):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def adherence(
    habit: HabitSpec,
    entries: Sequence[EntryView],
    from_date: date,
    to_date: date,
) -> float | None:
    if from_date > to_date:
        return None
    grouped = _group_by_bucket(_up_to(entries, to_date), habit.period)
    complete = [
        bucket
        for bucket in scheduled_buckets(habit, to_date)
        if bucket.is_complete(to_date)
        and ranges_intersect(bucket.start, bucket.end, from_date, to_date)
    ]
    if not complete:
        return None
    satisfied = sum(1 for bucket in complete if _bucket_satisfied(habit, grouped, bucket))
    return satisfied / len(complete)


def _up_to(entries: Sequence[EntryView], as_of: date) -> list[EntryView]:
    return [entry for entry in entries if entry.occurred_on <= as_of]


def _bucket_satisfied(
    habit: HabitSpec,
    grouped: dict[date | tuple[int, int], list[EntryView]],
    bucket: Bucket,
) -> bool:
    value = rollup(grouped.get(bucket.key, []), habit.aggregation)
    return is_satisfied(value, habit.comparator, habit.target_value)


def _group_by_bucket(
    entries: Sequence[EntryView],
    period: Period,
) -> dict[date | tuple[int, int], list[EntryView]]:
    grouped: dict[date | tuple[int, int], list[EntryView]] = defaultdict(list)
    for entry in entries:
        grouped[bucket_for(entry.occurred_on, period).key].append(entry)
    return grouped
