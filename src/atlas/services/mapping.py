from atlas.db.models import Entry, Goal, Habit, Metric, Milestone
from atlas.domain import (
    Aggregation,
    Comparator,
    EntryView,
    GoalKind,
    GoalSpec,
    HabitSpec,
    Measure,
    MilestoneView,
    Period,
)


def entry_view(entry: Entry) -> EntryView:
    return EntryView(
        occurred_on=entry.occurred_on,
        value_num=entry.value_num,
        value_bool=entry.value_bool,
        value_text=entry.value_text,
        occurred_at=entry.occurred_at,
        created_at=entry.created_at,
        id=entry.id,
    )


def habit_spec(habit: Habit, metric: Metric) -> HabitSpec:
    weekdays = frozenset(habit.weekdays) if habit.weekdays else None
    return HabitSpec(
        period=Period(habit.period),
        target_value=habit.target_value,
        comparator=Comparator(habit.comparator),
        aggregation=Aggregation(metric.aggregation),
        active_from=habit.active_from,
        active_to=habit.active_to,
        weekdays=weekdays,
    )


def goal_spec(goal: Goal) -> GoalSpec:
    measure = Measure(goal.measure) if goal.measure is not None else None
    comparator = Comparator(goal.comparator) if goal.comparator is not None else None
    return GoalSpec(
        kind=GoalKind(goal.kind),
        start_on=goal.start_on,
        due_on=goal.due_on,
        target_value=goal.target_value,
        comparator=comparator,
        baseline_value=goal.baseline_value,
        measure=measure,
    )


def milestone_view(milestone: Milestone) -> MilestoneView:
    return MilestoneView(
        name=milestone.name,
        due_on=milestone.due_on,
        done_at=milestone.done_at,
    )
