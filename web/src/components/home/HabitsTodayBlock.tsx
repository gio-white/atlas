import { HabitDayList } from '@/components/habits/HabitDayList'
import { NewHabitButton } from '@/components/habits/NewHabitButton'
import { useDayActions } from '@/components/habits/useDayActions'
import { PageError } from '@/components/PageState'
import { getHabitsDay, type HabitFreeze, type HabitsDay, listFreezes, listHabits } from '@/lib/api'
import { dayCountLabel } from '@/lib/habits'
import { todayIso } from '@/lib/utils'

import { BlockEmpty, HomeBlock } from './HomeBlock'

/** What Home's Habits block reads: the Day tab's view of the day, the freezes (for Unfreeze),
 * and whether any active habit exists (for the empty state). */
export type HabitsToday = { view: HabitsDay; freezes: HabitFreeze[]; hasHabits: boolean }

export async function loadHabitsToday(day: string): Promise<HabitsToday> {
  const [view, freezes, habits] = await Promise.all([
    getHabitsDay(day),
    listFreezes(),
    listHabits(),
  ])
  return { view, freezes, hasHabits: habits.some((habit) => habit.archived_at === null) }
}

/**
 * Home's Habits block (habits brief §10): the "As of" day's scheduled habits in the Day tab's
 * groups and order, with "3 of 6 done" beside the heading, which opens Habits → Day. Rows act as
 * on the Day tab: the icon ticks a habit you tick, the name opens the row menu. After a change
 * `onChanged` reloads Home, so Habits kept in This week so far follows.
 */
export function HabitsTodayBlock({
  habits,
  search,
  onChanged,
  className,
}: {
  habits: HabitsToday | null
  search: string
  onChanged: () => Promise<void>
  className?: string
}) {
  const actions = useDayActions(onChanged)
  const view = habits?.view
  return (
    <HomeBlock
      id="habits"
      title="Habits"
      to="/habits"
      aside={
        view !== undefined && view.total > 0 ? dayCountLabel(view.done, view.total) : undefined
      }
      search={search}
      unavailable={habits === null}
      className={className}
    >
      {habits === null || view === undefined ? null : !habits.hasHabits ? (
        <div className="flex flex-col items-start gap-2">
          <BlockEmpty>No habits yet</BlockEmpty>
          <NewHabitButton size="sm" />
        </div>
      ) : view.rows.length === 0 ? (
        <BlockEmpty>
          {view.day === todayIso()
            ? 'No habits scheduled today.'
            : 'No habits scheduled on this day.'}
        </BlockEmpty>
      ) : (
        <div className="flex flex-col gap-2">
          {actions.error !== null && <PageError message={actions.error} />}
          <HabitDayList view={view} freezes={habits.freezes} actions={actions} />
        </div>
      )}
    </HomeBlock>
  )
}
