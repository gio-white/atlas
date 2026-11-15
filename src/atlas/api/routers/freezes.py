from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import HabitFreezeCreate, HabitFreezeOut
from atlas.api.serialize import habit_freeze_out
from atlas.services import add_freeze, delete_freeze, list_freezes

router = APIRouter(prefix="/freezes", tags=["habits"])


@router.get("", response_model=list[HabitFreezeOut])
def get_freezes(session: SessionDep, habit: str | None = None) -> list[HabitFreezeOut]:
    """Freezes newest first; with `habit`, that habit's own and those for every habit."""
    return [habit_freeze_out(session, row) for row in list_freezes(session, habit_slug=habit)]


@router.post("", response_model=HabitFreezeOut, status_code=201)
def post_freeze(session: SessionDep, body: HabitFreezeCreate) -> HabitFreezeOut:
    row = add_freeze(
        session,
        start_on=body.start_on,
        end_on=body.end_on,
        reason=body.reason,
        habit_slug=body.habit,
    )
    return habit_freeze_out(session, row)


@router.delete("/{freeze_id}", status_code=204)
def delete_freeze_by_id(session: SessionDep, freeze_id: int) -> None:
    delete_freeze(session, freeze_id)
