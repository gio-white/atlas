from datetime import date

from fastapi import APIRouter, Response
from pydantic import BaseModel

from atlas.api.deps import SessionDep
from atlas.api.quest_schemas import (
    AmbitionCreate,
    AmbitionOut,
    AmbitionUpdate,
    ChapterCreate,
    ChapterOut,
    ChapterUpdate,
    CompleteRequest,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    MilestoneCreate,
    MilestoneOut,
    MilestoneUpdate,
    PromoteOut,
    SideQuestCreate,
    SideQuestOut,
    SideQuestUpdate,
    TaskCreate,
    TaskDetailOut,
    TaskOrganize,
    TaskOut,
    TaskPromote,
    TaskUpdate,
)
from atlas.domain import ParentKind, TaskStatus
from atlas.domain.quests import QuestKind
from atlas.services.quests import (
    complete_container,
    create_container,
    create_task,
    delete_container,
    delete_task,
    get_container,
    get_task,
    list_containers,
    list_tasks,
    organize_task,
    promote_task,
    reopen_container,
    update_container,
    update_task,
)

router = APIRouter(tags=["quests"])


def _container_routes(
    kind: QuestKind,
    prefix: str,
    create_model: type[BaseModel],
    update_model: type[BaseModel],
    out_model: type[BaseModel],
    *,
    listable: bool,
    completable: bool,
) -> None:
    label = kind.value.replace("_", " ")

    if listable:

        def list_items(
            session: SessionDep, include_archived: bool = False, ambition_id: int | None = None
        ) -> list[out_model]:
            rows = list_containers(
                session, kind, include_archived=include_archived, ambition_id=ambition_id
            )
            return [out_model.model_validate(row) for row in rows]

        if kind is not QuestKind.GOAL:

            def list_plain(session: SessionDep, include_archived: bool = False) -> list[out_model]:
                return list_items(session, include_archived=include_archived)

            router.get(prefix, response_model=list[out_model], summary=f"List {label}s")(list_plain)
        else:
            router.get(prefix, response_model=list[out_model], summary=f"List {label}s")(list_items)

    def create_item(session: SessionDep, body: create_model) -> out_model:
        view = create_container(session, kind, body.model_dump(exclude_unset=True))
        return out_model.model_validate(view)

    def read_item(session: SessionDep, item_id: int) -> out_model:
        return out_model.model_validate(get_container(session, kind, item_id))

    def patch_item(session: SessionDep, item_id: int, body: update_model) -> out_model:
        view = update_container(session, kind, item_id, body.model_dump(exclude_unset=True))
        return out_model.model_validate(view)

    def remove_item(session: SessionDep, item_id: int) -> Response:
        delete_container(session, kind, item_id)
        return Response(status_code=204)

    path = f"{prefix}/{{item_id}}"
    router.post(prefix, response_model=out_model, status_code=201, summary=f"Create a {label}")(
        create_item
    )
    router.get(path, response_model=out_model, summary=f"Read a {label}")(read_item)
    router.patch(path, response_model=out_model, summary=f"Edit, move, or archive a {label}")(
        patch_item
    )
    router.delete(path, status_code=204, summary=f"Delete an empty {label}")(remove_item)

    if completable:

        def complete_item(
            session: SessionDep, item_id: int, body: CompleteRequest | None = None
        ) -> out_model:
            override = body.override if body is not None else False
            view = complete_container(session, kind, item_id, override=override)
            return out_model.model_validate(view)

        def reopen_item(session: SessionDep, item_id: int) -> out_model:
            return out_model.model_validate(reopen_container(session, kind, item_id))

        router.post(f"{path}/complete", response_model=out_model, summary=f"Complete a {label}")(
            complete_item
        )
        router.post(f"{path}/reopen", response_model=out_model, summary=f"Reopen a {label}")(
            reopen_item
        )


_container_routes(
    QuestKind.AMBITION,
    "/ambitions",
    AmbitionCreate,
    AmbitionUpdate,
    AmbitionOut,
    listable=True,
    completable=True,
)
_container_routes(
    QuestKind.GOAL, "/goals", GoalCreate, GoalUpdate, GoalOut, listable=True, completable=True
)
_container_routes(
    QuestKind.MILESTONE,
    "/milestones",
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneOut,
    listable=False,
    completable=True,
)
_container_routes(
    QuestKind.SIDE_QUEST,
    "/side-quests",
    SideQuestCreate,
    SideQuestUpdate,
    SideQuestOut,
    listable=True,
    completable=True,
)
_container_routes(
    QuestKind.CHAPTER,
    "/chapters",
    ChapterCreate,
    ChapterUpdate,
    ChapterOut,
    listable=False,
    completable=False,
)


@router.get("/tasks", response_model=list[TaskOut], summary="List tasks")
def get_tasks(
    session: SessionDep,
    parent_kind: ParentKind | None = None,
    parent_id: int | None = None,
    status: TaskStatus | None = None,
    inbox: bool | None = None,
    standalone: bool | None = None,
    due_on: date | None = None,
    include_archived: bool = False,
) -> list[TaskOut]:
    rows = list_tasks(
        session,
        parent_kind=parent_kind,
        parent_id=parent_id,
        status=status,
        inbox=inbox,
        standalone=standalone,
        due_on=due_on,
        include_archived=include_archived,
    )
    return [TaskOut.model_validate(row) for row in rows]


@router.post("/tasks", response_model=TaskDetailOut, status_code=201, summary="Create a task")
def post_task(session: SessionDep, body: TaskCreate) -> TaskDetailOut:
    return TaskDetailOut.model_validate(create_task(session, **body.model_dump()))


@router.get("/tasks/{task_id}", response_model=TaskDetailOut, summary="Read a task")
def get_task_by_id(session: SessionDep, task_id: int) -> TaskDetailOut:
    return TaskDetailOut.model_validate(get_task(session, task_id))


@router.patch("/tasks/{task_id}", response_model=TaskDetailOut, summary="Edit a task")
def patch_task(session: SessionDep, task_id: int, body: TaskUpdate) -> TaskDetailOut:
    return TaskDetailOut.model_validate(
        update_task(session, task_id, body.model_dump(exclude_unset=True))
    )


@router.delete("/tasks/{task_id}", status_code=204, summary="Delete an Inbox task")
def remove_task(session: SessionDep, task_id: int) -> Response:
    delete_task(session, task_id)
    return Response(status_code=204)


@router.post(
    "/tasks/{task_id}/organize", response_model=TaskDetailOut, summary="Organize or move a task"
)
def post_organize(session: SessionDep, task_id: int, body: TaskOrganize) -> TaskDetailOut:
    return TaskDetailOut.model_validate(organize_task(session, task_id, **body.model_dump()))


@router.post(
    "/tasks/{task_id}/promote", response_model=PromoteOut, status_code=201, summary="Turn into…"
)
def post_promote(session: SessionDep, task_id: int, body: TaskPromote) -> PromoteOut:
    return PromoteOut.model_validate(promote_task(session, task_id, **body.model_dump()))
