from calendar import monthrange
from datetime import date, timedelta

from atlas.domain.enums import Period
from atlas.domain.models import Bucket


def bucket_key(occurred_on: date, period: Period) -> date | tuple[int, int]:
    match period:
        case Period.DAY:
            return occurred_on
        case Period.WEEK:
            iso = occurred_on.isocalendar()
            return (iso.year, iso.week)
        case Period.MONTH:
            return (occurred_on.year, occurred_on.month)


def bucket_for(occurred_on: date, period: Period) -> Bucket:
    key = bucket_key(occurred_on, period)
    start, end = _range_for(key, period)
    return Bucket(period=period, key=key, start=start, end=end)


def next_bucket(bucket: Bucket) -> Bucket:
    return bucket_for(bucket.end + timedelta(days=1), bucket.period)


def previous_bucket(bucket: Bucket) -> Bucket:
    return bucket_for(bucket.start - timedelta(days=1), bucket.period)


def ranges_intersect(start_a: date, end_a: date, start_b: date, end_b: date) -> bool:
    return start_a <= end_b and start_b <= end_a


def _range_for(key: date | tuple[int, int], period: Period) -> tuple[date, date]:
    if period is Period.DAY and isinstance(key, date):
        return key, key
    if period is Period.WEEK and isinstance(key, tuple):
        year, week = key
        return date.fromisocalendar(year, week, 1), date.fromisocalendar(year, week, 7)
    if period is Period.MONTH and isinstance(key, tuple):
        year, month = key
        return date(year, month, 1), date(year, month, monthrange(year, month)[1])
    raise TypeError(f"invalid bucket key {key!r} for period {period}")
