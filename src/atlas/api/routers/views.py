from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import AreaViewOut, TodayViewOut, WeekViewOut
from atlas.services import area_view, today_view, week_view

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/today", response_model=TodayViewOut)
def get_today(session: SessionDep, as_of: date | None = None) -> TodayViewOut:
    return TodayViewOut.model_validate(today_view(session, as_of=as_of))


@router.get("/week", response_model=WeekViewOut)
def get_week(session: SessionDep, as_of: date | None = None) -> WeekViewOut:
    return WeekViewOut.model_validate(week_view(session, as_of=as_of))


@router.get("/areas/{slug}", response_model=AreaViewOut)
def get_area_view(session: SessionDep, slug: str, as_of: date | None = None) -> AreaViewOut:
    return AreaViewOut.model_validate(area_view(session, slug, as_of=as_of))
