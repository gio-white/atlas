from collections.abc import Sequence
from datetime import date

from atlas.domain.enums import GoalKind, Measure, PaceStatus
from atlas.domain.habits import is_satisfied
from atlas.domain.models import EntryView, GoalProgress, GoalSpec, MilestoneView

PACE_TOLERANCE = 0.05


def goal_progress(
    goal: GoalSpec,
    entries: Sequence[EntryView],
    milestones: Sequence[MilestoneView],
    as_of: date,
) -> GoalProgress:
    if goal.kind is GoalKind.MILESTONE:
        return _milestone_progress(milestones)
    return _metric_progress(goal, entries, as_of)


def pace_status(goal: GoalSpec, progress: GoalProgress, as_of: date) -> PaceStatus:
    if progress.target_met:
        return PaceStatus.ACHIEVED
    if as_of > goal.due_on:
        return PaceStatus.OVERDUE
    if progress.fraction is None:
        return PaceStatus.NO_DATA
    elapsed = _elapsed_fraction(goal.start_on, goal.due_on, as_of)
    if progress.fraction > elapsed + PACE_TOLERANCE:
        return PaceStatus.AHEAD
    if progress.fraction < elapsed - PACE_TOLERANCE:
        return PaceStatus.BEHIND
    return PaceStatus.ON_TRACK


def _milestone_progress(milestones: Sequence[MilestoneView]) -> GoalProgress:
    total = len(milestones)
    if total == 0:
        return GoalProgress(current=None, baseline=None, fraction=None, target_met=False)
    done = sum(1 for milestone in milestones if milestone.is_done)
    return GoalProgress(
        current=float(done),
        baseline=0.0,
        fraction=done / total,
        target_met=done == total,
    )


def _metric_progress(
    goal: GoalSpec,
    entries: Sequence[EntryView],
    as_of: date,
) -> GoalProgress:
    if goal.target_value is None or goal.comparator is None or goal.measure is None:
        raise ValueError("metric_target goals require target_value, comparator, and measure")
    current = _current_value(goal, entries, as_of)
    baseline = _baseline(goal, entries, current)
    if current is None:
        target_met = False
    else:
        target_met = is_satisfied(current, goal.comparator, goal.target_value)
    fraction = _fraction(current, baseline, goal.target_value, target_met)
    return GoalProgress(
        current=current,
        baseline=baseline,
        fraction=fraction,
        target_met=target_met,
    )


def _current_value(goal: GoalSpec, entries: Sequence[EntryView], as_of: date) -> float | None:
    if goal.measure is Measure.LATEST_VALUE:
        relevant = [entry for entry in entries if entry.occurred_on <= as_of]
        if not relevant:
            return None
        latest = max(relevant, key=lambda entry: entry.recency_key())
        return latest.numeric_value()
    return _sum_in_window(entries, goal.start_on, as_of)


def _baseline(goal: GoalSpec, entries: Sequence[EntryView], current: float | None) -> float | None:
    if goal.baseline_value is not None:
        return goal.baseline_value
    if goal.measure is Measure.CUMULATIVE_SINCE_START:
        return 0.0
    relevant = [entry for entry in entries if entry.occurred_on <= goal.start_on]
    if not relevant:
        return current
    latest = max(relevant, key=lambda entry: entry.recency_key())
    return latest.numeric_value()


def _fraction(
    current: float | None,
    baseline: float | None,
    target: float,
    target_met: bool,
) -> float | None:
    if current is None or baseline is None:
        return None
    if target == baseline:
        return 1.0 if target_met else 0.0
    raw = (current - baseline) / (target - baseline)
    return max(0.0, min(1.0, raw))


def _elapsed_fraction(start_on: date, due_on: date, as_of: date) -> float:
    if due_on == start_on:
        return 1.0 if as_of >= start_on else 0.0
    raw = (as_of - start_on).days / (due_on - start_on).days
    return max(0.0, min(1.0, raw))


def _sum_in_window(entries: Sequence[EntryView], start_on: date, as_of: date) -> float:
    total = 0.0
    for entry in entries:
        if start_on <= entry.occurred_on <= as_of:
            value = entry.numeric_value()
            if value is not None:
                total += value
    return total
