from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import TaskCreate, TaskOut, TaskUpdate
from atlas.domain import TaskBucket
from atlas.services.tasks import create_task, list_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def get_tasks(
    session: SessionDep,
    bucket: TaskBucket | None = None,
    include_done: bool = False,
) -> list[TaskOut]:
    rows = list_tasks(session, bucket=bucket, include_done=include_done)
    return [TaskOut.model_validate(row) for row in rows]


@router.post("", response_model=TaskOut, status_code=201)
def post_task(session: SessionDep, body: TaskCreate) -> TaskOut:
    task = create_task(
        session,
        body.title,
        bucket=body.bucket,
        due_on=body.due_on,
        due_at=body.due_at,
        priority=body.priority,
    )
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(session: SessionDep, task_id: int, body: TaskUpdate) -> TaskOut:
    task = update_task(session, task_id, **body.model_dump(exclude_unset=True))
    return TaskOut.model_validate(task)
