from datetime import date

from atlas.domain import Period, bucket_for, bucket_key, next_bucket, previous_bucket


def test_day_bucket_is_the_date_itself():
    day = date(2026, 8, 13)
    bucket = bucket_for(day, Period.DAY)

    assert bucket_key(day, Period.DAY) == day
    assert bucket.start == bucket.end == day
    assert bucket.contains(day)
    assert not bucket.is_complete(day)
    assert bucket.is_in_progress(day)
    assert bucket.is_complete(date(2026, 8, 14))


def test_week_bucket_is_monday_through_sunday():
    thursday = date(2026, 8, 13)
    bucket = bucket_for(thursday, Period.WEEK)

    assert bucket_key(thursday, Period.WEEK) == (2026, 33)
    assert bucket.start == date(2026, 8, 10)
    assert bucket.end == date(2026, 8, 16)
    assert bucket.contains(date(2026, 8, 10))
    assert bucket.contains(date(2026, 8, 16))
    assert not bucket.contains(date(2026, 8, 17))
    assert bucket.is_in_progress(thursday)
    assert bucket.is_complete(date(2026, 8, 17))


def test_week_bucket_crosses_the_year_boundary():
    bucket = bucket_for(date(2026, 1, 1), Period.WEEK)

    assert bucket.start == date(2025, 12, 29)
    assert bucket.end == date(2026, 1, 4)
    assert bucket.key == (2026, 1)


def test_month_bucket_uses_the_calendar_month():
    bucket = bucket_for(date(2026, 2, 10), Period.MONTH)

    assert bucket_key(date(2026, 2, 10), Period.MONTH) == (2026, 2)
    assert bucket.start == date(2026, 2, 1)
    assert bucket.end == date(2026, 2, 28)
    assert bucket.is_in_progress(date(2026, 2, 28))
    assert bucket.is_complete(date(2026, 3, 1))


def test_next_and_previous_bucket_walk_periods():
    week = bucket_for(date(2026, 8, 13), Period.WEEK)

    assert next_bucket(week).start == date(2026, 8, 17)
    assert previous_bucket(week).end == date(2026, 8, 9)

    february = bucket_for(date(2026, 2, 10), Period.MONTH)
    assert next_bucket(february).key == (2026, 3)
    assert previous_bucket(february).key == (2026, 1)
