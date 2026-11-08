from collections.abc import Sequence

from atlas.db.models import Entry, Habit, HabitBreak, Metric
from atlas.domain import (
    Aggregation,
    Comparator,
    EntryView,
    HabitSpec,
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


def habit_spec(
    habit: Habit,
    metric: Metric,
    breaks: Sequence[HabitBreak] = (),
) -> HabitSpec:
    weekdays = frozenset(habit.weekdays) if habit.weekdays else None
    return HabitSpec(
        period=Period(habit.period),
        target_value=habit.target_value,
        comparator=Comparator(habit.comparator),
        aggregation=Aggregation(metric.aggregation),
        active_from=habit.active_from,
        active_to=habit.active_to,
        weekdays=weekdays,
        breaks=tuple((row.start_on, row.end_on) for row in breaks),
    )
