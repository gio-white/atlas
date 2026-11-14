import type { Habit } from '@/lib/api'
import { dueOn, ruleSummary, timeGroups } from '@/lib/habits'

import { BlockEmpty, HomeBlock } from './HomeBlock'

/**
 * Today's habits, read-only while the habits rebuild lands (docs/domain/home.md): the active
 * habits due on `asOf`, Morning to Any time, each with its rule. Ticking returns with the Day
 * screen.
 */
export function HabitsTodayBlock({
  habits,
  asOf,
  search,
  className,
}: {
  habits: Habit[] | null
  asOf: string
  search: string
  className?: string
}) {
  const active = (habits ?? []).filter((habit) => habit.archived_at === null)
  const weekday = ((new Date(`${asOf}T00:00:00`).getDay() + 6) % 7) + 1
  const due = timeGroups(active.filter((habit) => dueOn(habit.rule, weekday))).flatMap(
    (group) => group.habits,
  )
  return (
    <HomeBlock
      id="habits"
      title="Habits"
      action={{ label: 'All habits', to: '/habits' }}
      search={search}
      unavailable={habits === null}
      className={className}
    >
      {active.length === 0 ? (
        <BlockEmpty>No habits yet.</BlockEmpty>
      ) : due.length === 0 ? (
        <BlockEmpty>No habits scheduled today.</BlockEmpty>
      ) : (
        <ul className="flex flex-col gap-2">
          {due.map((habit) => (
            <li key={habit.slug} className="flex flex-col">
              <span className="text-sm font-medium text-ink">{habit.name}</span>
              <span className="text-xs text-muted">{ruleSummary(habit)}</span>
            </li>
          ))}
        </ul>
      )}
    </HomeBlock>
  )
}
