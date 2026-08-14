from datetime import date

from atlas.services import log_slip, slips_week


def test_log_slip_counts_this_week_and_sparkline(session):
    log_slip(session, occurred_on=date(2026, 8, 10))
    log_slip(session, occurred_on=date(2026, 8, 11))
    log_slip(session, occurred_on=date(2026, 8, 11))
    view = slips_week(session, as_of=date(2026, 8, 14))
    assert view.this_week == 3.0
    assert view.week_start == date(2026, 8, 10)
    assert view.series[0] == 1.0
    assert view.series[1] == 2.0
    assert view.last_week == 0.0
    assert view.delta_fraction is None


def test_slips_delta_against_previous_week(session):
    log_slip(session, occurred_on=date(2026, 8, 3))
    log_slip(session, occurred_on=date(2026, 8, 4))
    log_slip(session, occurred_on=date(2026, 8, 5))
    log_slip(session, occurred_on=date(2026, 8, 10))
    log_slip(session, occurred_on=date(2026, 8, 11))
    view = slips_week(session, as_of=date(2026, 8, 14))
    assert view.this_week == 2.0
    assert view.last_week == 3.0
    assert view.delta_fraction == -1 / 3
