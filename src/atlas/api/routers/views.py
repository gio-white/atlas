from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import HabitDetailOut, HabitsDayOut, HabitsWeekOut, ThisWeekOut, WeekSoFarOut
from atlas.api.serialize import habit_detail_out, habits_day_out, habits_week_out
from atlas.services import habit_detail, habits_day, habits_week, this_week, week_so_far

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/week-so-far", response_model=WeekSoFarOut)
def get_week_so_far(session: SessionDep, as_of: date | None = None) -> WeekSoFarOut:
    return WeekSoFarOut.model_validate(week_so_far(session, as_of=as_of))


@router.get("/this-week", response_model=ThisWeekOut)
def get_this_week(session: SessionDep, as_of: date | None = None) -> ThisWeekOut:
    return ThisWeekOut.model_validate(this_week(session, as_of=as_of))


@router.get("/habits/day", response_model=HabitsDayOut)
def get_habits_day(session: SessionDep, as_of: date | None = None) -> HabitsDayOut:
    return habits_day_out(habits_day(session, as_of=as_of))


@router.get("/habits/week", response_model=HabitsWeekOut)
def get_habits_week(session: SessionDep, as_of: date | None = None) -> HabitsWeekOut:
    return habits_week_out(habits_week(session, as_of=as_of))


# Singular, like the SPA's /habit/:slug: a habit called "day" or "week" stays reachable.
@router.get("/habit/{slug}", response_model=HabitDetailOut)
def get_habit_detail(slug: str, session: SessionDep, as_of: date | None = None) -> HabitDetailOut:
    return habit_detail_out(session, habit_detail(session, slug, as_of=as_of))
