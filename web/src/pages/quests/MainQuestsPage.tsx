import { Plus } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { GoalCard } from '@/components/quests/QuestCard'
import { QuestFormDialog } from '@/components/quests/QuestFormDialog'
import { LevelIcon, QuestBar, StatusChip } from '@/components/quests/QuestVisuals'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { TaskList } from '@/components/quests/TaskList'
import { useQuestView } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import { type AmbitionSection, getMainQuests } from '@/lib/api'
import { countLabel, doneTasksLabel, progressLabel, questDateLabel } from '@/lib/quests'

type Creating = { kind: 'ambition' } | { kind: 'goal'; ambitionId: number | null } | null

export function MainQuestsPage() {
  const { data, error, reload } = useQuestView(getMainQuests, "Couldn't load your main quests.")
  const [creating, setCreating] = useState<Creating>(null)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
  }, [reload])

  if (error !== null && data === null) {
    return <PageUnavailable title="Main quests" message={error} />
  }
  if (data === null) return <PageLoading />

  const empty = data.ambitions.length === 0 && data.independent_goals.length === 0

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <PageHeader
            title="Main quests"
            description="Your ambitions and the goals that move them forward."
          />
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreating({ kind: 'ambition' })}
            >
              <LevelIcon kind="ambition" />
              New ambition
            </Button>
            <Button
              type="button"
              className="bg-iris hover:bg-iris/90"
              onClick={() => setCreating({ kind: 'goal', ambitionId: null })}
            >
              <Plus className="size-4" aria-hidden />
              New goal
            </Button>
          </div>
        </div>

        {empty && (
          <EmptyState
            title="No main quests yet"
            hint="Start with an ambition, a broad direction, or go straight to a goal you want to reach."
          />
        )}

        {data.ambitions.map((section) => (
          <AmbitionBlock
            key={section.ambition.id}
            section={section}
            onChanged={refresh}
            onAddGoal={() => setCreating({ kind: 'goal', ambitionId: section.ambition.id })}
          />
        ))}

        {data.independent_goals.length > 0 && (
          <section aria-labelledby="independent-goals" className="flex flex-col gap-3">
            <h2
              id="independent-goals"
              className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
            >
              <LevelIcon kind="goal" />
              Independent goals
            </h2>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {data.independent_goals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
          </section>
        )}
      </div>
      <QuestFormDialog
        open={creating?.kind === 'ambition'}
        onOpenChange={(open) => !open && setCreating(null)}
        kind="ambition"
        onSaved={refresh}
      />
      <QuestFormDialog
        open={creating?.kind === 'goal'}
        onOpenChange={(open) => !open && setCreating(null)}
        kind="goal"
        parent={{
          kind: 'ambition',
          id: creating?.kind === 'goal' ? creating.ambitionId : null,
        }}
        onSaved={refresh}
      />
    </TaskDrawerProvider>
  )
}

function AmbitionBlock({
  section,
  onChanged,
  onAddGoal,
}: {
  section: AmbitionSection
  onChanged: () => void
  onAddGoal: () => void
}) {
  const { ambition, goals, tasks } = section
  const href = `/quests/ambitions/${ambition.id}`
  const done = doneTasksLabel(ambition.done_tasks, ambition.total_tasks)
  return (
    <section aria-labelledby={`ambition-${ambition.id}`} className="flex flex-col gap-3">
      <header className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <h2
            id={`ambition-${ambition.id}`}
            className="flex min-w-0 items-center gap-2 text-lg font-semibold tracking-tight text-ink"
          >
            <LevelIcon kind="ambition" className="size-5" label />
            <Link to={href} className="min-w-0 hover:underline">
              {ambition.title}
            </Link>
          </h2>
          {ambition.status !== 'active' && (
            <StatusChip status={ambition.status} openItems={ambition.completed_with_open_items} />
          )}
          <span className="text-xs text-muted">
            {[
              countLabel(ambition.goal_count, 'goal'),
              done,
              ambition.target_on === null ? null : `Target ${questDateLabel(ambition.target_on)}`,
            ]
              .filter(Boolean)
              .join(' · ')}
          </span>
        </div>
        {ambition.description !== null && (
          <p className="text-sm text-muted">{ambition.description}</p>
        )}
        {ambition.progress !== null && (
          <div className="flex max-w-md items-center gap-2">
            <QuestBar
              value={ambition.progress}
              completed={ambition.status === 'completed'}
              className="flex-1"
            />
            <span className="text-xs tabular-nums text-muted">
              {progressLabel(ambition.progress)}
            </span>
          </div>
        )}
      </header>

      {goals.length === 0 ? (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-dashed border-line px-4 py-4">
          <p className="min-w-0 flex-1 text-sm text-muted">
            No goals yet. What concrete outcome would move this forward?
          </p>
          <Button type="button" variant="outline" size="sm" onClick={onAddGoal}>
            <LevelIcon kind="goal" className="size-3.5" />
            Add a goal
          </Button>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {goals.map((goal) => (
            <GoalCard key={goal.id} goal={goal} />
          ))}
          <button
            type="button"
            className="flex min-h-24 items-center justify-center gap-2 rounded-2xl border border-dashed border-line text-sm text-muted hover:bg-raised/60 hover:text-ink"
            onClick={onAddGoal}
          >
            <Plus className="size-4" aria-hidden />
            Add a goal
          </button>
        </div>
      )}

      {tasks.length > 0 && (
        <div className="rounded-2xl border border-line bg-raised/40 px-2 py-2">
          <h3 className="flex items-center gap-2 px-2 pb-1 text-xs font-medium text-muted">
            Tasks directly on this ambition
          </h3>
          <TaskList tasks={tasks} onChanged={onChanged} reorderable={false} compact />
        </div>
      )}
    </section>
  )
}
