from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import EntryAmend, EntryCreate, EntryOut
from atlas.api.serialize import entry_out_for
from atlas.domain import Source
from atlas.services import amend_entry, delete_entry, log_entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=EntryOut, status_code=201)
def post_entry(session: SessionDep, body: EntryCreate) -> EntryOut:
    entry = log_entry(
        session,
        body.metric,
        body.value,
        occurred_on=body.occurred_on,
        occurred_at=body.occurred_at,
        note=body.note,
        source=Source.API,
    )
    return entry_out_for(session, entry)


@router.patch("/{entry_id}", response_model=EntryOut)
def patch_entry(session: SessionDep, entry_id: int, body: EntryAmend) -> EntryOut:
    entry = amend_entry(session, entry_id, **body.model_dump(exclude_unset=True))
    return entry_out_for(session, entry)


@router.delete("/{entry_id}", status_code=204)
def remove_entry(session: SessionDep, entry_id: int) -> None:
    delete_entry(session, entry_id)
