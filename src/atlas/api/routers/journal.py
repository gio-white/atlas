from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import EntryOut, JournalCreate, JournalDayOut
from atlas.api.serialize import entry_out_for
from atlas.domain import Source
from atlas.services.journal import journal_day, log_journal

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("", response_model=JournalDayOut)
def get_journal(session: SessionDep, as_of: date | None = None) -> JournalDayOut:
    return JournalDayOut.model_validate(journal_day(session, as_of=as_of))


@router.post("", response_model=EntryOut, status_code=201)
def post_journal(session: SessionDep, body: JournalCreate) -> EntryOut:
    entry = log_journal(
        session,
        body.text,
        occurred_on=body.occurred_on,
        source=Source.API,
    )
    return entry_out_for(session, entry)
