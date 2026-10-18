from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import SleepSessionCreate, SleepSessionOut, SleepViewOut
from atlas.api.serialize import sleep_session_out
from atlas.domain import SleepStageSpan, Source
from atlas.services import (
    delete_sleep_session,
    get_sleep_session,
    list_sleep_sessions,
    log_sleep_session,
    sleep_view,
)

router = APIRouter(prefix="/sleep", tags=["sleep"])


@router.get("/view", response_model=SleepViewOut)
def get_sleep_view(session: SessionDep, as_of: date | None = None) -> SleepViewOut:
    return SleepViewOut.model_validate(sleep_view(session, as_of=as_of))


@router.get("/sessions", response_model=list[SleepSessionOut])
def get_sessions(session: SessionDep, occurred_on: date | None = None) -> list[SleepSessionOut]:
    return [
        sleep_session_out(session, row)
        for row in list_sleep_sessions(session, occurred_on=occurred_on)
    ]


@router.post("/sessions", response_model=SleepSessionOut, status_code=201)
def post_session(session: SessionDep, body: SleepSessionCreate) -> SleepSessionOut:
    row = log_sleep_session(
        session,
        started_at=body.started_at,
        ended_at=body.ended_at,
        stages=[
            SleepStageSpan(stage=stage.stage, started_at=stage.started_at, ended_at=stage.ended_at)
            for stage in body.stages
        ],
        note=body.note,
        source=Source.API,
    )
    return sleep_session_out(session, row)


@router.get("/sessions/{session_id}", response_model=SleepSessionOut)
def get_session_by_id(session: SessionDep, session_id: int) -> SleepSessionOut:
    return sleep_session_out(session, get_sleep_session(session, session_id))


@router.delete("/sessions/{session_id}", status_code=204)
def remove_session(session: SessionDep, session_id: int) -> None:
    delete_sleep_session(session, session_id)
