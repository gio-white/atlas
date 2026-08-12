from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import GoalCreate, GoalOut, GoalProgressOut
from atlas.api.serialize import goals_out
from atlas.domain import GoalStatus
from atlas.services import MilestoneInput, create_goal, goal_progress, list_goals

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalOut])
def get_goals(
    session: SessionDep,
    area: str | None = None,
    status: GoalStatus | None = None,
) -> list[GoalOut]:
    return goals_out(session, list_goals(session, area_slug=area, status=status))


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
    )
    return goals_out(session, [goal])[0]


@router.get("/{slug}/progress", response_model=GoalProgressOut)
def get_goal_progress(
    session: SessionDep,
    slug: str,
    as_of: date | None = None,
) -> GoalProgressOut:
    return GoalProgressOut.model_validate(goal_progress(session, slug, as_of=as_of))
