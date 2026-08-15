from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    AreaViewOut,
    GoalsBoardOut,
    HabitsBoardOut,
    HabitsCalendarOut,
    HomeWeekOut,
    TodayViewOut,
    WeekViewOut,
)
from atlas.domain import Period
from atlas.services import (
    area_view,
    goals_board,
    habit_calendar,
    habits_board,
    home_week,
    today_view,
    week_view,
)

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/today", response_model=TodayViewOut)
def get_today(session: SessionDep, as_of: date | None = None) -> TodayViewOut:
    return TodayViewOut.model_validate(today_view(session, as_of=as_of))


@router.get("/week", response_model=WeekViewOut)
def get_week(session: SessionDep, as_of: date | None = None) -> WeekViewOut:
    return WeekViewOut.model_validate(week_view(session, as_of=as_of))


@router.get("/home", response_model=HomeWeekOut)
def get_home(session: SessionDep, as_of: date | None = None) -> HomeWeekOut:
    return HomeWeekOut.model_validate(home_week(session, as_of=as_of))


@router.get("/goals", response_model=GoalsBoardOut)
def get_goals_board(session: SessionDep, as_of: date | None = None) -> GoalsBoardOut:
    return GoalsBoardOut.model_validate(goals_board(session, as_of=as_of))


@router.get("/habits/calendar", response_model=HabitsCalendarOut)
def get_habits_calendar(
    session: SessionDep,
    period: Period = Period.WEEK,
    as_of: date | None = None,
) -> HabitsCalendarOut:
    return HabitsCalendarOut.model_validate(habit_calendar(session, period=period, as_of=as_of))


@router.get("/habits", response_model=HabitsBoardOut)
def get_habits_board(session: SessionDep, as_of: date | None = None) -> HabitsBoardOut:
    return HabitsBoardOut.model_validate(habits_board(session, as_of=as_of))


@router.get("/areas/{slug}", response_model=AreaViewOut)
def get_area_view(session: SessionDep, slug: str, as_of: date | None = None) -> AreaViewOut:
    return AreaViewOut.model_validate(area_view(session, slug, as_of=as_of))
