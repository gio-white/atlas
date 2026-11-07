from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from atlas.domain import (
    SleepSessionView,
    SleepStage,
    SleepStageSpan,
    resolve_sleep_session,
    sleep_week_math,
)

UTC_ZONE = ZoneInfo("UTC")


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=UTC)


def _span(stage: SleepStage, start: datetime, end: datetime) -> SleepStageSpan:
    return SleepStageSpan(stage=stage, started_at=start, ended_at=end)


def test_resolve_attributes_the_night_to_the_local_wake_date():
    spec = resolve_sleep_session(
        started_at=_at(12, 22, 30),
        ended_at=_at(13, 6, 30),
        stages=[],
        timezone=UTC_ZONE,
    )
    assert spec.occurred_on == date(2026, 8, 13)
    assert spec.minutes == 480


def test_resolve_uses_the_configured_zone_for_the_wake_date():
    spec = resolve_sleep_session(
        started_at=_at(12, 14),
        ended_at=_at(12, 23, 30),
        stages=[],
        timezone=ZoneInfo("Europe/Rome"),
    )
    assert spec.occurred_on == date(2026, 8, 13)


@pytest.mark.parametrize(
    ("stages", "message"),
    [
        ([_span(SleepStage.DEEP, _at(12, 21), _at(12, 23))], "inside the session"),
        ([_span(SleepStage.DEEP, _at(13, 1), _at(13, 1))], "end after"),
        (
            [
                _span(SleepStage.DEEP, _at(13, 1), _at(13, 2)),
                _span(SleepStage.REM, _at(13, 1, 30), _at(13, 3)),
            ],
            "overlap",
        ),
    ],
)
def test_resolve_rejects_bad_stages(stages, message):
    with pytest.raises(ValueError, match=message):
        resolve_sleep_session(
            started_at=_at(12, 22),
            ended_at=_at(13, 6),
            stages=stages,
            timezone=UTC_ZONE,
        )


def test_resolve_rejects_an_empty_interval():
    with pytest.raises(ValueError, match="after started_at"):
        resolve_sleep_session(
            started_at=_at(13, 6), ended_at=_at(13, 6), stages=[], timezone=UTC_ZONE
        )


def test_week_math_reports_last_night_stages_and_offsets():
    stages = (
        _span(SleepStage.AWAKE, _at(12, 23), _at(12, 23, 15)),
        _span(SleepStage.LIGHT, _at(12, 23, 15), _at(13, 1)),
        _span(SleepStage.DEEP, _at(13, 1), _at(13, 2, 30)),
        _span(SleepStage.REM, _at(13, 2, 30), _at(13, 3, 30)),
        _span(SleepStage.LIGHT, _at(13, 3, 30), _at(13, 7)),
    )
    night = SleepSessionView(
        id=1,
        started_at=_at(12, 23),
        ended_at=_at(13, 7),
        occurred_on=date(2026, 8, 13),
        stages=stages,
    )

    week = sleep_week_math([night], date(2026, 8, 13), UTC_ZONE)

    assert week.range_start == date(2026, 8, 7)
    assert [day.date for day in week.days][-1] == date(2026, 8, 13)
    assert week.nights_logged == 1
    last = week.night
    assert last is not None
    assert last.bed_offset == -60
    assert last.wake_offset == 420
    assert last.in_bed_minutes == 480
    assert last.stages.awake == 15
    assert last.stages.light == 105 + 210
    assert last.stages.deep == 90
    assert last.stages.rem == 60
    assert last.asleep_minutes == 465
    assert last.segments[0].start_offset == -60
    assert week.average_bed_offset == -60
    assert week.average_stages is not None


def test_week_math_picks_the_longest_session_per_day_and_averages_logged_nights():
    sessions = [
        SleepSessionView(
            id=1,
            started_at=_at(11, 23),
            ended_at=_at(12, 7),
            occurred_on=date(2026, 8, 12),
            stages=(),
        ),
        SleepSessionView(
            id=2,
            started_at=_at(12, 14),
            ended_at=_at(12, 14, 30),
            occurred_on=date(2026, 8, 12),
            stages=(),
        ),
        SleepSessionView(
            id=3,
            started_at=_at(13, 0),
            ended_at=_at(13, 6),
            occurred_on=date(2026, 8, 13),
            stages=(),
        ),
        SleepSessionView(
            id=4,
            started_at=_at(1, 23),
            ended_at=_at(2, 7),
            occurred_on=date(2026, 8, 2),
            stages=(),
        ),
    ]

    week = sleep_week_math(sessions, date(2026, 8, 13), UTC_ZONE)

    assert week.nights_logged == 2
    by_day = {day.date: day.night for day in week.days}
    assert by_day[date(2026, 8, 12)].session_id == 1
    assert by_day[date(2026, 8, 10)] is None
    assert week.average_asleep == (480 + 360) / 2
    assert week.average_bed_offset == (-60 + 0) / 2
    assert week.average_wake_offset == (420 + 360) / 2
    assert week.average_stages is None


def test_sleep_week_math_takes_a_window_and_measures_consistency():
    nights = [
        SleepSessionView(
            id=index,
            started_at=_at(day - 1, 23) + timedelta(minutes=offset),
            ended_at=_at(day, 7),
            occurred_on=date(2026, 8, day),
            stages=(),
            created_at=_at(day, 8),
        )
        for index, (day, offset) in enumerate(((10, 0), (12, 60)), start=1)
    ]

    window = sleep_week_math(nights, date(2026, 8, 13), UTC_ZONE, days=30)

    assert len(window.days) == 30
    assert window.range_start == date(2026, 7, 15)
    assert window.nights_logged == 2
    assert window.bed_spread == 30
    assert window.wake_spread == 0
    assert window.last_recorded_at == _at(12, 8)


def test_sleep_week_math_spread_needs_two_nights():
    week = sleep_week_math([], date(2026, 8, 13), UTC_ZONE)

    assert week.bed_spread is None
    assert week.last_recorded_at is None
    with pytest.raises(ValueError):
        sleep_week_math([], date(2026, 8, 13), UTC_ZONE, days=0)
