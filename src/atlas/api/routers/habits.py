from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.quest_schemas import HabitSupportCreate, HabitSupportOut
from atlas.api.schemas import (
    HabitCreate,
    HabitDayOut,
    HabitDaySet,
    HabitOut,
    HabitRuleIn,
    HabitUpdate,
)
from atlas.api.serialize import habit_out
from atlas.domain.quests import QuestKind
from atlas.services import (
    RuleInput,
    add_habit_support,
    archive_habit,
    clear_habit_day,
    create_habit,
    delete_habit,
    get_habit,
    list_habit_supports,
    list_habits,
    remove_habit_support,
    restore_habit,
    set_habit_day,
    update_habit,
)

router = APIRouter(prefix="/habits", tags=["habits"])


def _rule(body: HabitRuleIn) -> RuleInput:
    return RuleInput(
        frequency=body.frequency,
        check=body.check,
        weekdays=tuple(body.weekdays) if body.weekdays is not None else None,
        times=body.times,
        source=body.source,
        source_ref=body.source_ref,
        threshold=body.threshold,
        value=body.value,
    )


@router.get("", response_model=list[HabitOut])
def get_habits(session: SessionDep, include_archived: bool = True) -> list[HabitOut]:
    habits = list_habits(session, include_archived=include_archived)
    return [habit_out(session, habit) for habit in habits]


@router.post("", response_model=HabitOut, status_code=201)
def post_habit(session: SessionDep, body: HabitCreate) -> HabitOut:
    habit = create_habit(
        session,
        body.name,
        _rule(body.rule),
        slug=body.slug,
        time_of_day=body.time_of_day,
        first_day=body.first_day,
    )
    return habit_out(session, habit)


@router.put("/{slug}/days/{day}", response_model=HabitDayOut)
def put_habit_day(session: SessionDep, slug: str, day: date, body: HabitDaySet) -> HabitDayOut:
    mark = set_habit_day(session, slug, day, body.result)
    return HabitDayOut(day=day, result=mark.result if mark is not None else None)


@router.delete("/{slug}/days/{day}", status_code=204)
def delete_habit_day(session: SessionDep, slug: str, day: date) -> None:
    clear_habit_day(session, slug, day)


@router.get("/{slug}/supports", response_model=list[HabitSupportOut])
def get_supports(session: SessionDep, slug: str) -> list[HabitSupportOut]:
    return [HabitSupportOut.model_validate(item) for item in list_habit_supports(session, slug)]


@router.post("/{slug}/supports", response_model=HabitSupportOut, status_code=201)
def post_support(session: SessionDep, slug: str, body: HabitSupportCreate) -> HabitSupportOut:
    item = add_habit_support(session, slug, body.kind, body.id)
    return HabitSupportOut.model_validate(item)


@router.delete("/{slug}/supports/{kind}/{item_id}", status_code=204)
def delete_support(session: SessionDep, slug: str, kind: QuestKind, item_id: int) -> None:
    remove_habit_support(session, slug, kind, item_id)


@router.post("/{slug}/archive", response_model=HabitOut)
def post_archive(session: SessionDep, slug: str) -> HabitOut:
    return habit_out(session, archive_habit(session, slug))


@router.post("/{slug}/restore", response_model=HabitOut)
def post_restore(session: SessionDep, slug: str) -> HabitOut:
    return habit_out(session, restore_habit(session, slug))


@router.get("/{slug}", response_model=HabitOut)
def get_habit_by_slug(session: SessionDep, slug: str) -> HabitOut:
    return habit_out(session, get_habit(session, slug))


@router.patch("/{slug}", response_model=HabitOut)
def patch_habit(session: SessionDep, slug: str, body: HabitUpdate) -> HabitOut:
    habit = update_habit(
        session,
        slug,
        name=body.name,
        time_of_day=body.time_of_day,
        rule=_rule(body.rule) if body.rule is not None else None,
        apply=body.apply,
    )
    return habit_out(session, habit)


@router.delete("/{slug}", status_code=204)
def delete_habit_by_slug(session: SessionDep, slug: str) -> None:
    delete_habit(session, slug)
