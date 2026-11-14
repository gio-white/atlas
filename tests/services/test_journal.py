from datetime import date

from atlas.domain import MetricOrigin
from atlas.services import get_metric, journal_day, log_journal


def test_log_journal_returns_latest_text_for_the_day(session):
    first = log_journal(session, "  morning notes  ", occurred_on=date(2026, 8, 14))
    second = log_journal(session, "evening notes", occurred_on=date(2026, 8, 14))
    view = journal_day(session, as_of=date(2026, 8, 14))
    assert view.as_of == date(2026, 8, 14)
    assert view.text == "evening notes"
    assert view.entry_id == second.id
    assert first.value_text == "morning notes"


def test_journal_day_empty_creates_the_journal_metric(session):
    view = journal_day(session, as_of=date(2026, 8, 14))
    assert view.text is None
    assert view.entry_id is None
    metric = get_metric(session, "journal")
    assert metric.value_type == "text"
    assert MetricOrigin(metric.origin) is MetricOrigin.JOURNAL
