import { useEffect, useState } from 'react'

import { PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { ApiError, type Habit, listHabits } from '@/lib/api'
import { ruleSummary, timeGroups } from '@/lib/habits'

/**
 * Habits, for now a read-only list while the habits rebuild lands (docs/domain/habits.md,
 * Status): each habit's name and rule, grouped by time of day, then the archived ones. The Day
 * and Week screens, ticking, and the habit page replace it in the next phases.
 */
export function HabitsPage() {
  const [habits, setHabits] = useState<Habit[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listHabits()
      .then((rows) => {
        if (!cancelled) setHabits(rows)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load habits')
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (error !== null) return <PageUnavailable title="Habits" message={error} />
  if (habits === null) return <PageLoading />

  const active = habits.filter((habit) => habit.archived_at === null)
  const archived = habits.filter((habit) => habit.archived_at !== null)

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Habits"
        description="Your habits and their rules. Ticking them off comes back soon."
      />

      {active.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-raised/60 px-4 py-10 text-center">
          <p className="font-medium text-ink">No habits yet</p>
        </div>
      ) : (
        timeGroups(active).map((group) => (
          <HabitList key={group.id} title={group.label} habits={group.habits} />
        ))
      )}

      {archived.length > 0 ? <HabitList title="Archived" habits={archived} muted /> : null}
    </div>
  )
}

function HabitList({
  title,
  habits,
  muted = false,
}: {
  title: string
  habits: Habit[]
  muted?: boolean
}) {
  return (
    <section className="flex flex-col gap-2" aria-label={title}>
      <h2 className="text-xs font-semibold tracking-wide text-muted uppercase">{title}</h2>
      <ul className="divide-y divide-line rounded-2xl border border-line bg-surface">
        {habits.map((habit) => (
          <li key={habit.slug} className="flex flex-col gap-0.5 px-4 py-3">
            <span className={muted ? 'font-medium text-muted' : 'font-medium text-ink'}>
              {habit.name}
            </span>
            <span className="text-sm text-muted">{ruleSummary(habit)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
