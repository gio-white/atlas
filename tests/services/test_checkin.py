from datetime import date

from atlas.services import log_update, updates_status
from atlas.services.life import CHECKIN_HABIT_SLUG, CHECKIN_METRIC_SLUG, LIFE_AREA_SLUG


def test_log_update_creates_life_catalog_and_streak(session):
    first = log_update(session, occurred_on=date(2026, 8, 12))
    second = log_update(session, occurred_on=date(2026, 8, 13), note="showed up")
    assert first.value_bool is True
    assert second.note == "showed up"
    status = updates_status(session, as_of=date(2026, 8, 13))
    assert status.checked_in is True
    assert status.current_streak == 2
    assert status.longest_streak == 2
    from atlas.services import get_area, get_habit, get_metric

    assert get_area(session, LIFE_AREA_SLUG).slug == LIFE_AREA_SLUG
    assert get_metric(session, CHECKIN_METRIC_SLUG).value_type == "bool"
    metric = get_metric(session, CHECKIN_METRIC_SLUG)
    assert get_habit(session, CHECKIN_HABIT_SLUG).metric_id == metric.id


def test_updates_status_without_entries_is_open(session):
    status = updates_status(session, as_of=date(2026, 8, 14))
    assert status.checked_in is False
    assert status.current_streak == 0
