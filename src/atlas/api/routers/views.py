from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import ThisWeekOut, WeekSoFarOut
from atlas.services import this_week, week_so_far

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/week-so-far", response_model=WeekSoFarOut)
def get_week_so_far(session: SessionDep, as_of: date | None = None) -> WeekSoFarOut:
    return WeekSoFarOut.model_validate(week_so_far(session, as_of=as_of))


@router.get("/this-week", response_model=ThisWeekOut)
def get_this_week(session: SessionDep, as_of: date | None = None) -> ThisWeekOut:
    return ThisWeekOut.model_validate(this_week(session, as_of=as_of))
