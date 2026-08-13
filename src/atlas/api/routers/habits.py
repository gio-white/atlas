from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import HabitCreate, HabitOut, HabitStatusOut, HabitUpdate
from atlas.api.serialize import habits_out
from atlas.services import create_habit, get_habit, habit_status, list_habits, update_habit

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("", response_model=list[HabitOut])
def get_habits(session: SessionDep, metric: str | None = None) -> list[HabitOut]:
    return habits_out(session, list_habits(session, metric_slug=metric))


@router.post("", response_model=HabitOut, status_code=201)
def post_habit(session: SessionDep, body: HabitCreate) -> HabitOut:
    habit = create_habit(
        session,
        body.slug,
        metric_slug=body.metric,
        period=body.period,
        target_value=body.target_value,
        comparator=body.comparator,
        name=body.name,
        weekdays=body.weekdays,
        active_from=body.active_from,
        active_to=body.active_to,
    )
    return habits_out(session, [habit])[0]


@router.get("/{slug}/status", response_model=HabitStatusOut)
def get_habit_status(
    session: SessionDep,
    slug: str,
    as_of: date | None = None,
) -> HabitStatusOut:
    return HabitStatusOut.model_validate(habit_status(session, slug, as_of=as_of))


@router.get("/{slug}", response_model=HabitOut)
def get_habit_by_slug(session: SessionDep, slug: str) -> HabitOut:
    return habits_out(session, [get_habit(session, slug)])[0]


@router.patch("/{slug}", response_model=HabitOut)
def patch_habit(session: SessionDep, slug: str, body: HabitUpdate) -> HabitOut:
    habit = update_habit(session, slug, **body.model_dump(exclude_unset=True))
    return habits_out(session, [habit])[0]
