from dataclasses import dataclass
from datetime import date

from sqlmodel import Session

from atlas.db.models import Entry
from atlas.domain import Aggregation, Direction, Source, ValueType
from atlas.services.clock import resolve_today
from atlas.services.entries import log_entry
from atlas.services.errors import ValidationError
from atlas.services.life import JOURNAL_METRIC_SLUG, ensure_life_metric
from atlas.services.lookups import entries_for_metric
from atlas.services.mapping import entry_view


@dataclass(frozen=True, slots=True)
class JournalDay:
    as_of: date
    text: str | None
    entry_id: int | None


def ensure_journal_metric(session: Session):
    return ensure_life_metric(
        session,
        JOURNAL_METRIC_SLUG,
        value_type=ValueType.TEXT,
        aggregation=Aggregation.LAST,
        direction=Direction.NEUTRAL,
        name="Journal",
    )


def log_journal(
    session: Session,
    text: str,
    *,
    occurred_on: date | None = None,
    source: Source = Source.CLI,
) -> Entry:
    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("journal text must not be empty")
    ensure_journal_metric(session)
    return log_entry(
        session,
        JOURNAL_METRIC_SLUG,
        cleaned,
        occurred_on=occurred_on,
        source=source,
    )


def journal_day(session: Session, *, as_of: date | None = None) -> JournalDay:
    as_of = resolve_today(as_of)
    metric = ensure_journal_metric(session)
    on_day = [
        entry_view(entry)
        for entry in entries_for_metric(session, metric.id)
        if entry.occurred_on == as_of
    ]
    if not on_day:
        return JournalDay(as_of=as_of, text=None, entry_id=None)
    latest = max(on_day, key=lambda row: row.recency_key())
    return JournalDay(as_of=as_of, text=latest.value_text, entry_id=latest.id)
