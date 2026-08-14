from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import EntryOut, SlipCreate, SlipsWeekOut
from atlas.api.serialize import entry_out_for
from atlas.domain import Source
from atlas.services.slips import log_slip, slips_week

router = APIRouter(prefix="/slips", tags=["slips"])


@router.get("", response_model=SlipsWeekOut)
def get_slips(session: SessionDep, as_of: date | None = None) -> SlipsWeekOut:
    return SlipsWeekOut.model_validate(slips_week(session, as_of=as_of))


@router.post("", response_model=EntryOut, status_code=201)
def post_slip(session: SessionDep, body: SlipCreate) -> EntryOut:
    entry = log_slip(
        session,
        note=body.note,
        occurred_on=body.occurred_on,
        source=Source.API,
    )
    return entry_out_for(session, entry)
