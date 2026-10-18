from collections.abc import Sequence
from datetime import UTC, date, datetime

from sqlmodel import Session, col, select

from atlas.db.models import SleepSession, SleepSessionStage
from atlas.domain import (
    SleepSessionView,
    SleepStage,
    SleepStageSpan,
    SleepWeekMath,
    Source,
    resolve_sleep_session,
    sleep_week_math,
)
from atlas.services.clock import resolve_today
from atlas.services.errors import ValidationError
from atlas.services.lookups import require_sleep_session
from atlas.settings import load_settings


def log_sleep_session(
    session: Session,
    *,
    started_at: datetime,
    ended_at: datetime,
    stages: Sequence[SleepStageSpan] = (),
    note: str | None = None,
    source: Source = Source.CLI,
) -> SleepSession:
    try:
        resolved = resolve_sleep_session(
            started_at=started_at,
            ended_at=ended_at,
            stages=stages,
            timezone=load_settings().timezone,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    row = SleepSession(
        started_at=resolved.started_at,
        ended_at=resolved.ended_at,
        occurred_on=resolved.occurred_on,
        note=note,
        source=source,
    )
    session.add(row)
    session.flush()
    for span in resolved.stages:
        session.add(
            SleepSessionStage(
                session_id=row.id,
                stage=span.stage,
                started_at=span.started_at,
                ended_at=span.ended_at,
            )
        )
    session.commit()
    session.refresh(row)
    return row


def get_sleep_session(session: Session, session_id: int) -> SleepSession:
    return require_sleep_session(session, session_id)


def list_sleep_sessions(
    session: Session,
    *,
    occurred_on: date | None = None,
) -> list[SleepSession]:
    statement = select(SleepSession).order_by(SleepSession.started_at, SleepSession.id)
    if occurred_on is not None:
        statement = statement.where(SleepSession.occurred_on == occurred_on)
    return list(session.exec(statement).all())


def sleep_stages(session: Session, session_id: int | None) -> list[SleepSessionStage]:
    statement = (
        select(SleepSessionStage)
        .where(SleepSessionStage.session_id == session_id)
        .order_by(SleepSessionStage.started_at)
    )
    return list(session.exec(statement).all())


def delete_sleep_session(session: Session, session_id: int) -> None:
    row = require_sleep_session(session, session_id)
    for stage in sleep_stages(session, row.id):
        session.delete(stage)
    session.flush()
    session.delete(row)
    session.commit()


def sleep_view(session: Session, *, as_of: date | None = None) -> SleepWeekMath:
    as_of = resolve_today(as_of)
    return sleep_week_math(_session_views(session), as_of, load_settings().timezone)


def _session_views(session: Session) -> list[SleepSessionView]:
    rows = list_sleep_sessions(session)
    ids = [row.id for row in rows]
    stages_by_session: dict[int | None, list[SleepStageSpan]] = {}
    if ids:
        statement = (
            select(SleepSessionStage)
            .where(col(SleepSessionStage.session_id).in_(ids))
            .order_by(SleepSessionStage.started_at)
        )
        for stage in session.exec(statement).all():
            stages_by_session.setdefault(stage.session_id, []).append(
                SleepStageSpan(
                    stage=SleepStage(stage.stage),
                    started_at=_coerce_utc(stage.started_at),
                    ended_at=_coerce_utc(stage.ended_at),
                )
            )
    return [
        SleepSessionView(
            id=row.id,
            started_at=_coerce_utc(row.started_at),
            ended_at=_coerce_utc(row.ended_at),
            occurred_on=row.occurred_on,
            stages=tuple(stages_by_session.get(row.id, [])),
            note=row.note,
        )
        for row in rows
    ]


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
