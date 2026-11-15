import type { HabitFreeze, HabitsDay } from '@/lib/api'
import { dayGroups, ownDayFreeze } from '@/lib/habits'

import { HabitDayRow } from './HabitDayRow'
import type { useDayActions } from './useDayActions'

/**
 * A day's scheduled habits by time of day (habits brief §7), shared by the Day tab and Home's
 * Habits block so both list the same rows in the same groups and order, and act the same way.
 * Group headings show only when some habit has a time of day.
 */
export function HabitDayList({
  view,
  freezes,
  actions,
}: {
  view: HabitsDay
  freezes: HabitFreeze[]
  actions: ReturnType<typeof useDayActions>
}) {
  return dayGroups(view.rows).map((group) => (
    <section key={group.id} aria-label={group.label ?? 'Habits'} className="flex flex-col gap-1">
      {group.label !== null && (
        <h3 className="px-1 text-xs font-semibold tracking-wide text-muted uppercase">
          {group.label}
        </h3>
      )}
      <ul className="-mx-2 flex flex-col md:mx-0">
        {group.rows.map((row) => (
          <HabitDayRow
            key={row.habit.slug}
            row={row}
            busy={actions.isBusy(row.habit.slug, view.day)}
            canUnfreeze={ownDayFreeze(freezes, row.habit.slug, view.day) !== undefined}
            onToggle={() => actions.toggle(row.habit.slug, row.result)}
            onAction={(action) => actions.act(row.habit.slug, view.day, action, freezes)}
          />
        ))}
      </ul>
    </section>
  ))
}
