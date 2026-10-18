from datetime import UTC, date, datetime

import pytest

from atlas.domain import SleepStage, SleepStageSpan
from atlas.services import (
    NotFoundError,
    ValidationError,
    delete_sleep_session,
    get_sleep_session,
    list_sleep_sessions,
    log_sleep_session,
    sleep_stages,
    sleep_view,
)


@pytest.fixture(autouse=True)
def _utc(monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")


def _night(session, day: int, *, staged: bool = True):
    start = datetime(2026, 8, day - 1, 23, 0, tzinfo=UTC)
    end = datetime(2026, 8, day, 7, 0, tzinfo=UTC)
    stages = (
        [
            SleepStageSpan(SleepStage.LIGHT, start, datetime(2026, 8, day, 1, 0, tzinfo=UTC)),
            SleepStageSpan(
                SleepStage.DEEP,
                datetime(2026, 8, day, 1, 0, tzinfo=UTC),
                datetime(2026, 8, day, 3, 0, tzinfo=UTC),
            ),
            SleepStageSpan(SleepStage.REM, datetime(2026, 8, day, 3, 0, tzinfo=UTC), end),
        ]
        if staged
        else []
    )
    return log_sleep_session(session, started_at=start, ended_at=end, stages=stages)


def test_log_sleep_session_stores_the_night_and_its_stages(session):
    row = _night(session, 13)

    assert row.occurred_on == date(2026, 8, 13)
    assert [stage.stage for stage in sleep_stages(session, row.id)] == [
        SleepStage.LIGHT,
        SleepStage.DEEP,
        SleepStage.REM,
    ]
    assert [item.id for item in list_sleep_sessions(session, occurred_on=date(2026, 8, 13))] == [
        row.id
    ]


def test_log_sleep_session_rejects_stages_outside_the_night(session):
    with pytest.raises(ValidationError, match="inside the session"):
        log_sleep_session(
            session,
            started_at=datetime(2026, 8, 12, 23, 0, tzinfo=UTC),
            ended_at=datetime(2026, 8, 13, 7, 0, tzinfo=UTC),
            stages=[
                SleepStageSpan(
                    SleepStage.DEEP,
                    datetime(2026, 8, 13, 6, 0, tzinfo=UTC),
                    datetime(2026, 8, 13, 8, 0, tzinfo=UTC),
                )
            ],
        )


def test_sleep_view_reads_last_night_and_the_week(session):
    _night(session, 11, staged=False)
    _night(session, 13)

    view = sleep_view(session, as_of=date(2026, 8, 13))

    assert view.night is not None
    assert view.night.stages.deep == 120
    assert view.nights_logged == 2
    assert len(view.days) == 7


def test_delete_sleep_session_removes_its_stages(session):
    row = _night(session, 13)
    delete_sleep_session(session, row.id)

    assert sleep_stages(session, row.id) == []
    with pytest.raises(NotFoundError):
        get_sleep_session(session, row.id)
