from dataclasses import dataclass
from datetime import date

from sqlmodel import Session

from atlas.db.models import Entry
from atlas.domain import Source
from atlas.services.clock import resolve_today
from atlas.services.entries import log_entry
from atlas.services.habits import habit_status
from atlas.services.life import CHECKIN_HABIT_SLUG, CHECKIN_METRIC_SLUG, ensure_checkin_habit


@dataclass(frozen=True, slots=True)
class UpdatesStatus:
    as_of: date
    checked_in: bool
    current_streak: int
    longest_streak: int


def log_update(
    session: Session,
    *,
    note: str | None = None,
    occurred_on: date | None = None,
    source: Source = Source.CLI,
) -> Entry:
    ensure_checkin_habit(session)
    return log_entry(
        session,
        CHECKIN_METRIC_SLUG,
        True,
        occurred_on=occurred_on,
        note=note,
        source=source,
    )


def updates_status(session: Session, *, as_of: date | None = None) -> UpdatesStatus:
    as_of = resolve_today(as_of)
    ensure_checkin_habit(session)
    status = habit_status(session, CHECKIN_HABIT_SLUG, as_of=as_of)
    return UpdatesStatus(
        as_of=status.as_of,
        checked_in=status.satisfied,
        current_streak=status.current_streak,
        longest_streak=status.longest_streak,
    )
