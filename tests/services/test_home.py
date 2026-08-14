from datetime import date

from atlas.domain import ScreenJudgment
from atlas.services import (
    create_screen_app,
    create_screen_category,
    home_week,
    log_entry,
    log_slip,
    log_update,
)


def test_home_week_empty_is_zeros(session):
    view = home_week(session, as_of=date(2026, 8, 14))
    assert view.week_start == date(2026, 8, 10)
    assert view.updates == 0
    assert view.slips == 0
    assert view.focus_minutes == 0
    assert view.tasks_done == 0
    assert view.updates_delta is None
    assert view.series_updates == [0.0] * 7
    assert view.series_slips == [0.0] * 7


def test_home_week_counts_live_widgets(session):
    log_update(session, occurred_on=date(2026, 8, 3))
    log_update(session, occurred_on=date(2026, 8, 10))
    log_update(session, occurred_on=date(2026, 8, 11))
    log_slip(session, occurred_on=date(2026, 8, 4))
    log_slip(session, occurred_on=date(2026, 8, 11))
    log_slip(session, occurred_on=date(2026, 8, 12))
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "instagram", category_slug="entertainment")
    log_entry(session, "instagram", 30, occurred_on=date(2026, 8, 4))
    log_entry(session, "instagram", 60, occurred_on=date(2026, 8, 11))

    view = home_week(session, as_of=date(2026, 8, 14))
    assert view.updates == 2
    assert view.updates_last_week == 1
    assert view.updates_delta == 1.0
    assert view.slips == 2
    assert view.slips_last_week == 1
    assert view.slips_delta == 1.0
    assert view.focus_minutes == 60
    assert view.focus_minutes_last_week == 30
    assert view.focus_delta == 1.0
    assert view.series_updates[0] == 1.0
    assert view.series_updates[1] == 1.0
    assert view.series_slips[1] == 1.0
    assert view.series_slips[2] == 1.0
