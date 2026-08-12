from datetime import date

import pytest

from atlas.domain import Source
from atlas.services import (
    NotFoundError,
    ValidationError,
    amend_entry,
    archive_metric,
    delete_entry,
    log_entry,
)
from atlas.settings import load_settings
from tests.services.helpers import seed_health


def test_log_entry_stores_numeric_value_against_the_metric(session):
    seed_health(session)
    entry = log_entry(
        session,
        "pushups",
        40,
        occurred_on=date(2026, 8, 10),
        note="post-travel",
        source=Source.CLI,
    )

    assert entry.id is not None
    assert entry.value_num == 40.0
    assert entry.value_bool is None
    assert entry.occurred_on == date(2026, 8, 10)
    assert entry.note == "post-travel"
    assert entry.source is Source.CLI
    assert entry.created_at is not None


def test_log_bool_metric_without_a_value_is_true(session):
    seed_health(session)
    entry = log_entry(session, "meditated", occurred_on=date(2026, 8, 13))

    assert entry.value_bool is True
    assert entry.value_num is None


def test_log_entry_defaults_occurred_on_to_today(session):
    seed_health(session)
    entry = log_entry(session, "meditated")

    assert entry.occurred_on == load_settings().today()


def test_multiple_entries_per_day_are_allowed(session):
    seed_health(session)
    first = log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))
    second = log_entry(session, "pushups", 20, occurred_on=date(2026, 8, 13))

    assert first.id != second.id


def test_cannot_log_to_an_archived_metric(session):
    seed_health(session)
    archive_metric(session, "pushups")

    with pytest.raises(ValidationError, match="archived"):
        log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))


def test_count_metric_requires_a_numeric_value(session):
    seed_health(session)

    with pytest.raises(ValidationError, match="numeric"):
        log_entry(session, "pushups", occurred_on=date(2026, 8, 13))


def test_amend_entry_updates_value_and_note(session):
    seed_health(session)
    entry = log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))

    amended = amend_entry(session, entry.id, value=40, note="fixed")

    assert amended.value_num == 40.0
    assert amended.note == "fixed"
    assert amended.occurred_on == date(2026, 8, 13)


def test_amend_can_move_the_occurrence_date(session):
    seed_health(session)
    entry = log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))

    amended = amend_entry(session, entry.id, occurred_on=date(2026, 8, 10))

    assert amended.occurred_on == date(2026, 8, 10)
    assert amended.value_num == 10.0


def test_delete_entry_removes_the_row(session):
    seed_health(session)
    entry = log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))

    delete_entry(session, entry.id)

    with pytest.raises(NotFoundError, match="entry"):
        delete_entry(session, entry.id)


def test_unknown_metric_is_not_found(session):
    with pytest.raises(NotFoundError, match="metric"):
        log_entry(session, "missing", 1)
