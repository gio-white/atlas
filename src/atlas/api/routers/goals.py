from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    GoalCreate,
    GoalDetailOut,
    GoalOut,
    GoalProgressOut,
    GoalUpdate,
    MilestoneOut,
)
from atlas.api.serialize import goal_detail_out, goals_out, milestone_out
from atlas.domain import GoalHorizon, GoalStatus
from atlas.services import (
    MilestoneInput,
    create_goal,
    get_goal_detail,
    goal_progress,
    list_goals,
    toggle_milestone,
    update_goal,
)

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalOut])
def get_goals(
    session: SessionDep,
    area: str | None = None,
    status: GoalStatus | None = None,
    horizon: GoalHorizon | None = None,
    parent: str | None = None,
) -> list[GoalOut]:
    return goals_out(
        session,
        list_goals(session, area_slug=area, status=status, horizon=horizon, parent_slug=parent),
    )


@router.post("", response_model=GoalOut, status_code=201)
def post_goal(session: SessionDep, body: GoalCreate) -> GoalOut:
    milestones = None
    if body.milestones is not None:
        milestones = [
            MilestoneInput(name=item.name, due_on=item.due_on) for item in body.milestones
        ]
    goal = create_goal(
        session,
        body.slug,
        area_slug=body.area,
        kind=body.kind,
        start_on=body.start_on,
        due_on=body.due_on,
        name=body.name,
        metric_slug=body.metric,
        target_value=body.target_value,
        comparator=body.comparator,
        baseline_value=body.baseline_value,
        measure=body.measure,
        milestones=milestones,
        horizon=body.horizon,
        parent_slug=body.parent,
        description=body.description,
    )
    return goals_out(session, [goal])[0]


@router.get("/{slug}/progress", response_model=GoalProgressOut)
def get_goal_progress(
    session: SessionDep,
    slug: str,
    as_of: date | None = None,
) -> GoalProgressOut:
    return GoalProgressOut.model_validate(goal_progress(session, slug, as_of=as_of))


@router.get("/{slug}", response_model=GoalDetailOut)
def get_goal_by_slug(session: SessionDep, slug: str) -> GoalDetailOut:
    return goal_detail_out(session, get_goal_detail(session, slug))


@router.patch("/{slug}", response_model=GoalOut)
def patch_goal(session: SessionDep, slug: str, body: GoalUpdate) -> GoalOut:
    data = body.model_dump(exclude_unset=True)
    if "parent" in data:
        data["parent_slug"] = data.pop("parent")
    goal = update_goal(session, slug, **data)
    return goals_out(session, [goal])[0]


@router.post("/{slug}/milestones/{name}/toggle", response_model=MilestoneOut)
def post_toggle_milestone(
    session: SessionDep,
    slug: str,
    name: str,
    done: bool | None = None,
    as_of: date | None = None,
) -> MilestoneOut:
    return milestone_out(toggle_milestone(session, slug, name, done=done, as_of=as_of))
