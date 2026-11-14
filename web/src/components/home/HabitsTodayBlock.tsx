import { HabitCard } from '@/components/habits/HabitCard'
import type { HabitsBoard } from '@/lib/api'
import { periodHabits, todayGroups } from '@/lib/habits'
import { flattenHabits } from '@/lib/habitsSummary'

import { BlockEmpty, HomeBlock } from './HomeBlock'

/**
 * The habits to act on today: daily habits scheduled today, then weekly and monthly ones, which
 * show their progress for the period ("2 of 4 this week"). Each keeps the Habits page's one-tap
 * Mark done or Log value. The Monday–Sunday grid lives on the Habits page.
 */
export function HabitsTodayBlock({
  board,
  asOf,
  search,
  onChanged,
  className,
}: {
  board: HabitsBoard | null
  asOf: string
  search: string
  onChanged: () => Promise<void>
  className?: string
}) {
  const statuses = board === null ? [] : flattenHabits(board)
  const daily = todayGroups(statuses).flatMap((group) => group.habits)
  const periodic = periodHabits(statuses)
  const due = [...daily, ...periodic]
  return (
    <HomeBlock
      id="habits"
      title="Habits"
      action={{ label: 'All habits', to: '/habit' }}
      search={search}
      unavailable={board === null}
      className={className}
    >
      {statuses.length === 0 ? (
        <BlockEmpty>No habits yet.</BlockEmpty>
      ) : due.length === 0 ? (
        <BlockEmpty>No habits scheduled today.</BlockEmpty>
      ) : (
        <ul className="flex flex-col gap-2">
          {due.map((status) => (
            <li key={status.slug}>
              <HabitCard
                status={status}
                asOf={asOf}
                search={search}
                onChanged={onChanged}
                layout="row"
              />
            </li>
          ))}
        </ul>
      )}
    </HomeBlock>
  )
}
