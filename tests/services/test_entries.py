from datetime import date

import pytest

from atlas.domain import ScreenJudgment, Source
from atlas.services import (
    NotFoundError,
    ValidationError,
    amend_entry,
    archive_metric,
    create_screen_app,
    create_screen_category,
    delete_entry,
    list_entries,
    log_entry,
    log_screen_session,
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


def test_list_entries_is_newest_first_with_metric_slugs(session):
    seed_health(session)
    older = log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 10))
    weight = log_entry(session, "weight", 78.4, occurred_on=date(2026, 8, 12))
    newer = log_entry(session, "pushups", 20, occurred_on=date(2026, 8, 12))

    rows = list_entries(session)

    assert [(entry.id, slug) for entry, slug in rows] == [
        (newer.id, "pushups"),
        (weight.id, "weight"),
        (older.id, "pushups"),
    ]


def test_list_entries_filters_by_metric_and_date_range(session):
    seed_health(session)
    log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 9))
    kept = log_entry(session, "pushups", 20, occurred_on=date(2026, 8, 11))
    log_entry(session, "weight", 78.4, occurred_on=date(2026, 8, 11))

    rows = list_entries(
        session, metric_slug="pushups", start_on=date(2026, 8, 10), end_on=date(2026, 8, 12)
    )
    assert [entry.id for entry, _ in rows] == [kept.id]
    assert len(list_entries(session)) == 3
    assert len(list_entries(session, limit=2)) == 2


def test_list_entries_rejects_bad_filters(session):
    seed_health(session)
    with pytest.raises(NotFoundError):
        list_entries(session, metric_slug="missing")
    with pytest.raises(ValidationError, match="start_on"):
        list_entries(session, start_on=date(2026, 8, 12), end_on=date(2026, 8, 10))
    with pytest.raises(ValidationError, match="limit"):
        list_entries(session, limit=0)


def test_list_entries_can_leave_out_automatic_data(session):
    seed_health(session)
    create_screen_category(session, "social", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "instagram", category_slug="social")
    log_entry(session, "pushups", 10, occurred_on=date(2026, 8, 13))
    log_screen_session(session, "instagram", minutes=25, occurred_on=date(2026, 8, 13))

    everything = list_entries(session)
    typed = list_entries(session, include_automatic=False)

    assert {slug for _, slug in everything} == {"pushups", "instagram"}
    assert [slug for _, slug in typed] == ["pushups"]
