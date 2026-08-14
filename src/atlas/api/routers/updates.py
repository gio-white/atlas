from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import EntryOut, UpdateCreate, UpdatesStatusOut
from atlas.api.serialize import entry_out_for
from atlas.domain import Source
from atlas.services.updates import log_update, updates_status

router = APIRouter(prefix="/updates", tags=["updates"])


@router.get("", response_model=UpdatesStatusOut)
def get_updates(session: SessionDep, as_of: date | None = None) -> UpdatesStatusOut:
    return UpdatesStatusOut.model_validate(updates_status(session, as_of=as_of))


@router.post("", response_model=EntryOut, status_code=201)
def post_update(session: SessionDep, body: UpdateCreate) -> EntryOut:
    entry = log_update(
        session,
        note=body.note,
        occurred_on=body.occurred_on,
        source=Source.API,
    )
    return entry_out_for(session, entry)
