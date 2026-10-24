from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    HabitBreakCreate,
    HabitBreakOut,
    HabitCheckInCreate,
    HabitCreate,
    HabitDaySet,
    HabitDetailOut,
    HabitOut,
    HabitStatusOut,
    HabitUpdate,
)
from atlas.api.serialize import habit_detail_out, habits_out
from atlas.domain import Source
from atlas.services import (
    add_habit_break,
    archive_habit,
    check_in,
    create_habit,
    delete_habit,
    delete_habit_break,
    get_habit,
    habit_detail,
    habit_status,
    list_habit_breaks,
    list_habits,
    set_habit_day,
    unarchive_habit,
    undo_check_in,
    update_habit,
)

router = APIRouter(prefix="/habits", tags=["habits"])


@router.get("", response_model=list[HabitOut])
def get_habits(
    session: SessionDep,
    metric: str | None = None,
    include_archived: bool = True,
) -> list[HabitOut]:
    habits = list_habits(session, metric_slug=metric, include_archived=include_archived)
    return habits_out(session, habits)


@router.post("", response_model=HabitOut, status_code=201)
def post_habit(session: SessionDep, body: HabitCreate) -> HabitOut:
    habit = create_habit(
        session,
        body.slug,
        name=body.name,
        kind=body.kind,
        metric_slug=body.metric,
        period=body.period,
        target_value=body.target_value,
        comparator=body.comparator,
        unit=body.unit,
        weekdays=body.weekdays,
        time_of_day=body.time_of_day,
        goal_slug=body.goal,
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


@router.get("/{slug}/detail", response_model=HabitDetailOut)
def get_habit_detail(
    session: SessionDep,
    slug: str,
    as_of: date | None = None,
) -> HabitDetailOut:
    return habit_detail_out(session, habit_detail(session, slug, as_of=as_of))


@router.put("/{slug}/days/{day}", response_model=HabitStatusOut)
def put_habit_day(
    session: SessionDep,
    slug: str,
    day: date,
    body: HabitDaySet,
    as_of: date | None = None,
) -> HabitStatusOut:
    status = set_habit_day(session, slug, day, done=body.done, as_of=as_of, source=Source.API)
    return HabitStatusOut.model_validate(status)


@router.post("/{slug}/checkins", response_model=HabitStatusOut, status_code=201)
def post_check_in(
    session: SessionDep,
    slug: str,
    body: HabitCheckInCreate,
    as_of: date | None = None,
) -> HabitStatusOut:
    status = check_in(
        session,
        slug,
        amount=body.amount,
        on=body.on,
        note=body.note,
        as_of=as_of,
        source=Source.API,
    )
    return HabitStatusOut.model_validate(status)


@router.delete("/{slug}/checkins/last", response_model=HabitStatusOut)
def delete_last_check_in(
    session: SessionDep,
    slug: str,
    on: date | None = None,
    as_of: date | None = None,
) -> HabitStatusOut:
    return HabitStatusOut.model_validate(undo_check_in(session, slug, on=on, as_of=as_of))


@router.get("/{slug}/breaks", response_model=list[HabitBreakOut])
def get_breaks(session: SessionDep, slug: str) -> list[HabitBreakOut]:
    return [HabitBreakOut.model_validate(row) for row in list_habit_breaks(session, slug)]


@router.post("/{slug}/breaks", response_model=HabitBreakOut, status_code=201)
def post_break(session: SessionDep, slug: str, body: HabitBreakCreate) -> HabitBreakOut:
    row = add_habit_break(session, slug, body.start_on, body.end_on, note=body.note)
    return HabitBreakOut.model_validate(row)


@router.delete("/{slug}/breaks/{break_id}", status_code=204)
def delete_break(session: SessionDep, slug: str, break_id: int) -> None:
    delete_habit_break(session, slug, break_id)


@router.post("/{slug}/archive", response_model=HabitOut)
def post_archive(session: SessionDep, slug: str) -> HabitOut:
    return habits_out(session, [archive_habit(session, slug)])[0]


@router.post("/{slug}/unarchive", response_model=HabitOut)
def post_unarchive(session: SessionDep, slug: str) -> HabitOut:
    return habits_out(session, [unarchive_habit(session, slug)])[0]


@router.get("/{slug}", response_model=HabitOut)
def get_habit_by_slug(session: SessionDep, slug: str) -> HabitOut:
    return habits_out(session, [get_habit(session, slug)])[0]


@router.patch("/{slug}", response_model=HabitOut)
def patch_habit(session: SessionDep, slug: str, body: HabitUpdate) -> HabitOut:
    fields = body.model_dump(exclude_unset=True)
    if "goal" in fields:
        fields["goal_slug"] = fields.pop("goal")
    habit = update_habit(session, slug, **fields)
    return habits_out(session, [habit])[0]


@router.delete("/{slug}", status_code=204)
def delete_habit_by_slug(session: SessionDep, slug: str) -> None:
    delete_habit(session, slug)
