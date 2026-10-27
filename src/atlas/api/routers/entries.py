from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from atlas.api.deps import SessionDep
from atlas.api.schemas import EntryAmend, EntryCreate, EntryOut
from atlas.api.serialize import entry_out, entry_out_for
from atlas.domain import Source
from atlas.services import amend_entry, delete_entry, list_entries, log_entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("", response_model=list[EntryOut])
def get_entries(
    session: SessionDep,
    metric: str | None = None,
    area: str | None = None,
    start_on: date | None = None,
    end_on: date | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[EntryOut]:
    rows = list_entries(
        session,
        metric_slug=metric,
        area_slug=area,
        start_on=start_on,
        end_on=end_on,
        limit=limit,
    )
    return [entry_out(entry, slug) for entry, slug in rows]


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
