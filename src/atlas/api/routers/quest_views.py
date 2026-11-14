from datetime import date, datetime

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.quest_schemas import (
    AmbitionSectionOut,
    GoalTreeOut,
    InboxOut,
    MainQuestsOut,
    PlanOut,
    SideQuestsOut,
    SideQuestTreeOut,
    TodayOut,
)
from atlas.services.quest_views import (
    ambition_view,
    goal_view,
    inbox_view,
    main_quests_view,
    plan_view,
    side_quest_view,
    side_quests_view,
    today_view,
)

router = APIRouter(prefix="/views", tags=["quest views"])


@router.get("/main-quests", response_model=MainQuestsOut)
def get_main_quests(session: SessionDep, include_archived: bool = False) -> MainQuestsOut:
    return MainQuestsOut.model_validate(
        main_quests_view(session, include_archived=include_archived)
    )


@router.get("/ambitions/{ambition_id}", response_model=AmbitionSectionOut)
def get_ambition_view(
    session: SessionDep, ambition_id: int, include_archived: bool = False
) -> AmbitionSectionOut:
    return AmbitionSectionOut.model_validate(
        ambition_view(session, ambition_id, include_archived=include_archived)
    )


@router.get("/goals/{goal_id}", response_model=GoalTreeOut)
def get_goal_view(session: SessionDep, goal_id: int, include_archived: bool = False) -> GoalTreeOut:
    return GoalTreeOut.model_validate(
        goal_view(session, goal_id, include_archived=include_archived)
    )


@router.get("/side-quests", response_model=SideQuestsOut)
def get_side_quests(session: SessionDep, include_archived: bool = False) -> SideQuestsOut:
    return SideQuestsOut.model_validate(
        side_quests_view(session, include_archived=include_archived)
    )


@router.get("/side-quests/{side_quest_id}", response_model=SideQuestTreeOut)
def get_side_quest_view(
    session: SessionDep, side_quest_id: int, include_archived: bool = False
) -> SideQuestTreeOut:
    return SideQuestTreeOut.model_validate(
        side_quest_view(session, side_quest_id, include_archived=include_archived)
    )


@router.get("/inbox", response_model=InboxOut)
def get_inbox(session: SessionDep) -> InboxOut:
    return InboxOut.model_validate(inbox_view(session))


@router.get("/today", response_model=TodayOut)
def get_today(session: SessionDep, as_of: date | None = None) -> TodayOut:
    return TodayOut.model_validate(today_view(session, as_of=as_of))


@router.get("/plan", response_model=PlanOut)
def get_plan(session: SessionDep, start: datetime, end: datetime) -> PlanOut:
    return PlanOut.model_validate(plan_view(session, start=start, end=end))
