from datetime import date

from atlas.services import get_metric, journal_day, list_areas, log_journal


def test_log_journal_returns_latest_text_for_the_day(session):
    first = log_journal(session, "  morning notes  ", occurred_on=date(2026, 8, 14))
    second = log_journal(session, "evening notes", occurred_on=date(2026, 8, 14))
    view = journal_day(session, as_of=date(2026, 8, 14))
    assert view.as_of == date(2026, 8, 14)
    assert view.text == "evening notes"
    assert view.entry_id == second.id
    assert first.value_text == "morning notes"


def test_journal_day_empty_creates_catalog(session):
    view = journal_day(session, as_of=date(2026, 8, 14))
    assert view.text is None
    assert view.entry_id is None
    assert get_metric(session, "journal").value_type == "text"
    assert "life" in {area.slug for area in list_areas(session)}
