from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    AreaViewOut,
    GoalsBoardOut,
    HabitsBoardOut,
    HabitsCalendarOut,
)
from atlas.domain import Period
from atlas.services import (
    area_view,
    goals_board,
    habit_calendar,
    habits_board,
)

router = APIRouter(prefix="/views", tags=["views"])


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
