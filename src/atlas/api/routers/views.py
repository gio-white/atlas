from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    HabitsBoardOut,
    HabitsCalendarOut,
    ThisWeekOut,
    WeekSoFarOut,
)
from atlas.domain import Period
from atlas.services import (
    habit_calendar,
    habits_board,
    this_week,
    week_so_far,
)

router = APIRouter(prefix="/views", tags=["views"])


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


@router.get("/week-so-far", response_model=WeekSoFarOut)
def get_week_so_far(session: SessionDep, as_of: date | None = None) -> WeekSoFarOut:
    return WeekSoFarOut.model_validate(week_so_far(session, as_of=as_of))


@router.get("/this-week", response_model=ThisWeekOut)
def get_this_week(session: SessionDep, as_of: date | None = None) -> ThisWeekOut:
    return ThisWeekOut.model_validate(this_week(session, as_of=as_of))
