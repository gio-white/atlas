from datetime import date

from atlas.domain import (
    GoalHorizon,
    PaceStatus,
    infer_horizon,
    is_column_on_track,
    parent_horizon_is_valid,
    required_parent_horizon,
)


def test_infer_horizon_from_window_length():
    start = date(2026, 1, 1)
    assert infer_horizon(start, date(2027, 1, 1)) is GoalHorizon.LONG
    assert infer_horizon(start, date(2026, 3, 1)) is GoalHorizon.MEDIUM
    assert infer_horizon(start, date(2026, 1, 8)) is GoalHorizon.SHORT


def test_parent_horizon_rules():
    assert required_parent_horizon(GoalHorizon.LONG) is None
    assert required_parent_horizon(GoalHorizon.MEDIUM) is GoalHorizon.LONG
    assert required_parent_horizon(GoalHorizon.SHORT) is GoalHorizon.MEDIUM
    assert parent_horizon_is_valid(GoalHorizon.LONG, None)
    assert not parent_horizon_is_valid(GoalHorizon.LONG, GoalHorizon.LONG)
    assert parent_horizon_is_valid(GoalHorizon.MEDIUM, None)
    assert parent_horizon_is_valid(GoalHorizon.MEDIUM, GoalHorizon.LONG)
    assert not parent_horizon_is_valid(GoalHorizon.MEDIUM, GoalHorizon.MEDIUM)
    assert parent_horizon_is_valid(GoalHorizon.SHORT, GoalHorizon.MEDIUM)
    assert not parent_horizon_is_valid(GoalHorizon.SHORT, GoalHorizon.LONG)


def test_column_on_track_includes_ahead_and_achieved():
    assert is_column_on_track(PaceStatus.ON_TRACK)
    assert is_column_on_track(PaceStatus.AHEAD)
    assert is_column_on_track(PaceStatus.ACHIEVED)
    assert not is_column_on_track(PaceStatus.BEHIND)
    assert not is_column_on_track(PaceStatus.NO_DATA)
