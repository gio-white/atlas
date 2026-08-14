from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import TaskCreate, TaskOut, TaskUpdate
from atlas.api.serialize import tasks_out
from atlas.domain import TaskBucket
from atlas.services.tasks import create_task, list_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def get_tasks(
    session: SessionDep,
    bucket: TaskBucket | None = None,
    include_done: bool = False,
    goal: str | None = None,
) -> list[TaskOut]:
    rows = list_tasks(session, bucket=bucket, include_done=include_done, goal_slug=goal)
    return tasks_out(session, rows)


@router.post("", response_model=TaskOut, status_code=201)
def post_task(session: SessionDep, body: TaskCreate) -> TaskOut:
    task = create_task(
        session,
        body.title,
        bucket=body.bucket,
        due_on=body.due_on,
        due_at=body.due_at,
        priority=body.priority,
        goal_slug=body.goal,
    )
    return tasks_out(session, [task])[0]


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(session: SessionDep, task_id: int, body: TaskUpdate) -> TaskOut:
    data = body.model_dump(exclude_unset=True)
    if "goal" in data:
        data["goal_slug"] = data.pop("goal")
    task = update_task(session, task_id, **data)
    return tasks_out(session, [task])[0]
