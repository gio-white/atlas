from datetime import date

from atlas.domain import ScreenJudgment
from atlas.services import (
    create_screen_app,
    create_screen_category,
    home_week,
    log_entry,
)


def test_home_week_empty_is_zeros(session):
    view = home_week(session, as_of=date(2026, 8, 14))
    assert view.week_start == date(2026, 8, 10)
    assert view.focus_minutes == 0
    assert view.tasks_done == 0
    assert view.focus_delta is None
    assert view.tasks_delta is None


def test_home_week_counts_screen_minutes(session):
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    create_screen_app(session, "instagram", category_slug="entertainment")
    log_entry(session, "instagram", 30, occurred_on=date(2026, 8, 4))
    log_entry(session, "instagram", 60, occurred_on=date(2026, 8, 11))

    view = home_week(session, as_of=date(2026, 8, 14))
    assert view.focus_minutes == 60
    assert view.focus_minutes_last_week == 30
    assert view.focus_delta == 1.0
