from datetime import UTC, date, datetime

from atlas.domain import (
    Comparator,
    EntryView,
    GoalKind,
    GoalProgress,
    GoalSpec,
    Measure,
    MilestoneView,
    PaceStatus,
    goal_progress,
    pace_status,
)


def _metric_goal(
    *,
    start_on: date = date(2026, 1, 1),
    due_on: date = date(2026, 12, 31),
    target_value: float = 75.0,
    comparator: Comparator = Comparator.AT_MOST,
    measure: Measure = Measure.LATEST_VALUE,
    baseline_value: float | None = None,
) -> GoalSpec:
    return GoalSpec(
        kind=GoalKind.METRIC_TARGET,
        start_on=start_on,
        due_on=due_on,
        target_value=target_value,
        comparator=comparator,
        measure=measure,
        baseline_value=baseline_value,
    )


def test_latest_value_uses_the_most_recent_entry_on_or_before_as_of():
    goal = _metric_goal()
    entries = [
        EntryView(occurred_on=date(2026, 1, 1), value_num=80),
        EntryView(occurred_on=date(2026, 6, 1), value_num=78),
        EntryView(occurred_on=date(2026, 8, 1), value_num=76),
    ]

    progress = goal_progress(goal, entries, [], date(2026, 7, 1))

    assert progress.current == 78
    assert progress.baseline == 80
    assert progress.fraction == 0.4
    assert progress.target_met is False


def test_latest_value_with_no_history_starts_at_zero_percent():
    goal = _metric_goal(target_value=75.0, comparator=Comparator.AT_MOST)
    entries = [EntryView(occurred_on=date(2026, 8, 1), value_num=80)]

    progress = goal_progress(goal, entries, [], date(2026, 8, 1))

    assert progress.current == 80
    assert progress.baseline == 80
    assert progress.fraction == 0.0
    assert progress.target_met is False


def test_latest_value_with_no_entries_has_no_fraction():
    goal = _metric_goal()

    progress = goal_progress(goal, [], [], date(2026, 8, 1))

    assert progress.current is None
    assert progress.fraction is None
    assert progress.target_met is False


def test_explicit_baseline_wins_over_inferred_history():
    goal = _metric_goal(baseline_value=90.0)
    entries = [
        EntryView(occurred_on=date(2026, 1, 1), value_num=80),
        EntryView(occurred_on=date(2026, 8, 1), value_num=75),
    ]

    progress = goal_progress(goal, entries, [], date(2026, 8, 1))

    assert progress.baseline == 90.0
    assert progress.fraction == 1.0
    assert progress.target_met is True


def test_cumulative_sums_from_start_with_zero_baseline():
    goal = _metric_goal(
        target_value=12.0,
        comparator=Comparator.AT_LEAST,
        measure=Measure.CUMULATIVE_SINCE_START,
        baseline_value=None,
    )
    entries = [
        EntryView(occurred_on=date(2025, 12, 31), value_num=5),
        EntryView(occurred_on=date(2026, 2, 1), value_num=3),
        EntryView(occurred_on=date(2026, 8, 1), value_num=4),
        EntryView(occurred_on=date(2026, 8, 20), value_num=2),
    ]

    progress = goal_progress(goal, entries, [], date(2026, 8, 13))

    assert progress.current == 7.0
    assert progress.baseline == 0.0
    assert progress.fraction == 7 / 12
    assert progress.target_met is False


def test_fraction_clamps_and_target_equals_baseline():
    already_there = _metric_goal(
        target_value=80.0, baseline_value=80.0, comparator=Comparator.AT_MOST
    )
    entries = [EntryView(occurred_on=date(2026, 1, 1), value_num=80)]
    met = goal_progress(already_there, entries, [], date(2026, 8, 1))
    assert met.fraction == 1.0
    assert met.target_met is True

    missed = _metric_goal(target_value=80.0, baseline_value=80.0, comparator=Comparator.AT_LEAST)
    not_met = goal_progress(
        missed,
        [EntryView(occurred_on=date(2026, 1, 1), value_num=70)],
        [],
        date(2026, 8, 1),
    )
    assert not_met.fraction == 0.0
    assert not_met.target_met is False

    overshot = _metric_goal(target_value=75.0, baseline_value=80.0)
    past = goal_progress(
        overshot,
        [EntryView(occurred_on=date(2026, 8, 1), value_num=70)],
        [],
        date(2026, 8, 1),
    )
    assert past.fraction == 1.0
    assert past.target_met is True


def test_milestone_progress_is_done_over_total():
    goal = GoalSpec(kind=GoalKind.MILESTONE, start_on=date(2026, 1, 1), due_on=date(2026, 12, 31))
    milestones = [
        MilestoneView(name="outline", done_at=datetime(2026, 2, 1, tzinfo=UTC)),
        MilestoneView(name="draft"),
        MilestoneView(name="ship"),
    ]

    progress = goal_progress(goal, [], milestones, date(2026, 8, 1))

    assert progress.current == 1.0
    assert progress.fraction == 1 / 3
    assert progress.target_met is False

    empty = goal_progress(goal, [], [], date(2026, 8, 1))
    assert empty.fraction is None
    assert empty.target_met is False


def test_milestone_target_is_met_when_every_checkpoint_is_done():
    goal = GoalSpec(kind=GoalKind.MILESTONE, start_on=date(2026, 1, 1), due_on=date(2026, 6, 1))
    done = datetime(2026, 5, 1, tzinfo=UTC)
    milestones = [
        MilestoneView(name="a", done_at=done),
        MilestoneView(name="b", done_at=done),
    ]

    progress = goal_progress(goal, [], milestones, date(2026, 8, 1))

    assert progress.fraction == 1.0
    assert progress.target_met is True
    assert pace_status(goal, progress, date(2026, 8, 1)) is PaceStatus.ACHIEVED


def test_pace_status_uses_elapsed_time_and_tolerance():
    goal = _metric_goal(start_on=date(2026, 1, 1), due_on=date(2026, 1, 11))
    # elapsed on Jan 6 is 5/10 = 0.5
    as_of = date(2026, 1, 6)

    assert pace_status(goal, GoalProgress(50, 0, 0.56, False), as_of) is PaceStatus.AHEAD
    assert pace_status(goal, GoalProgress(50, 0, 0.50, False), as_of) is PaceStatus.ON_TRACK
    assert pace_status(goal, GoalProgress(50, 0, 0.44, False), as_of) is PaceStatus.BEHIND
    assert pace_status(goal, GoalProgress(None, None, None, False), as_of) is PaceStatus.NO_DATA
    assert (
        pace_status(goal, GoalProgress(50, 0, 0.9, False), date(2026, 1, 12)) is PaceStatus.OVERDUE
    )
    assert (
        pace_status(goal, GoalProgress(75, 80, 1.0, True), date(2026, 1, 12)) is PaceStatus.ACHIEVED
    )


def test_same_day_goal_is_fully_elapsed_from_the_start_date():
    goal = _metric_goal(start_on=date(2026, 8, 13), due_on=date(2026, 8, 13))
    progress = GoalProgress(current=0.0, baseline=0.0, fraction=0.0, target_met=False)

    assert pace_status(goal, progress, date(2026, 8, 12)) is PaceStatus.ON_TRACK
    assert pace_status(goal, progress, date(2026, 8, 13)) is PaceStatus.BEHIND
