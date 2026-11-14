from datetime import datetime

from fastapi import APIRouter, Response

from atlas.api.deps import SessionDep
from atlas.api.quest_schemas import TimeBlockCreate, TimeBlockOut, TimeBlockUpdate
from atlas.services.time_blocks import (
    cancel_time_block,
    complete_time_block,
    create_time_block,
    delete_time_block,
    list_time_blocks,
    miss_time_block,
    update_time_block,
)

router = APIRouter(prefix="/time-blocks", tags=["time blocks"])


@router.get("", response_model=list[TimeBlockOut])
def get_time_blocks(
    session: SessionDep,
    start: datetime | None = None,
    end: datetime | None = None,
    task_id: int | None = None,
) -> list[TimeBlockOut]:
    rows = list_time_blocks(session, start=start, end=end, task_id=task_id)
    return [TimeBlockOut.model_validate(row) for row in rows]


@router.post("", response_model=TimeBlockOut, status_code=201)
def post_time_block(session: SessionDep, body: TimeBlockCreate) -> TimeBlockOut:
    return TimeBlockOut.model_validate(create_time_block(session, **body.model_dump()))


@router.patch("/{block_id}", response_model=TimeBlockOut)
def patch_time_block(session: SessionDep, block_id: int, body: TimeBlockUpdate) -> TimeBlockOut:
    return TimeBlockOut.model_validate(
        update_time_block(session, block_id, **body.model_dump(exclude_unset=True))
    )


@router.delete("/{block_id}", status_code=204)
def remove_time_block(session: SessionDep, block_id: int) -> Response:
    delete_time_block(session, block_id)
    return Response(status_code=204)


@router.post("/{block_id}/complete", response_model=TimeBlockOut)
def post_complete(session: SessionDep, block_id: int) -> TimeBlockOut:
    return TimeBlockOut.model_validate(complete_time_block(session, block_id))


@router.post("/{block_id}/cancel", response_model=TimeBlockOut)
def post_cancel(session: SessionDep, block_id: int) -> TimeBlockOut:
    return TimeBlockOut.model_validate(cancel_time_block(session, block_id))


@router.post("/{block_id}/miss", response_model=TimeBlockOut)
def post_miss(session: SessionDep, block_id: int) -> TimeBlockOut:
    return TimeBlockOut.model_validate(miss_time_block(session, block_id))
