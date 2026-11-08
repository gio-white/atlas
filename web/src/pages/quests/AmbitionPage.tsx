import { Pencil, Plus } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PageLoading, PageUnavailable } from '@/components/PageState'
import { CompletionControl } from '@/components/quests/CompletionControl'
import { GoalCard } from '@/components/quests/QuestCard'
import { QuestFormDialog } from '@/components/quests/QuestFormDialog'
import { LevelIcon, QuestBreadcrumb, QuestRing, StatusChip } from '@/components/quests/QuestVisuals'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { MoveButtons, moveSibling, TaskList } from '@/components/quests/TaskList'
import { errorMessage, useQuestView } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import { getAmbitionView, updateQuestGoal } from '@/lib/api'
import { countLabel, doneTasksLabel, questDateLabel } from '@/lib/quests'

export function AmbitionPage() {
  const id = Number(useParams().id)
  const load = useCallback(() => getAmbitionView(id), [id])
  const { data, error, reload } = useQuestView(load, "Couldn't load this ambition.")
  const [editing, setEditing] = useState(false)
  const [addingGoal, setAddingGoal] = useState(false)
  const [moveError, setMoveError] = useState<string | null>(null)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
  }, [reload])

  if (error !== null && data === null) {
    return <PageUnavailable title="Ambition" message={error} />
  }
  if (data === null || data.ambition.id !== id) return <PageLoading />

  const { ambition, goals, tasks } = data
  const done = doneTasksLabel(ambition.done_tasks, ambition.total_tasks)

  async function moveGoal(index: number, direction: -1 | 1) {
    setMoveError(null)
    try {
      await moveSibling(goals, index, direction, (goalId, position) =>
        updateQuestGoal(goalId, { position }),
      )
    } catch (caught) {
      setMoveError(errorMessage(caught, "Couldn't reorder the goals."))
    } finally {
      refresh()
    }
  }

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-6">
        <QuestBreadcrumb
          root={{ label: 'Main quests', to: '/quests' }}
          path={[]}
          current={ambition.title}
        />
        <header className="flex flex-wrap items-start gap-4">
          <QuestRing value={ambition.progress} completed={ambition.status === 'completed'} />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 text-xs font-medium text-iris">
              <LevelIcon kind="ambition" className="size-3.5" />
              Ambition
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{ambition.title}</h1>
            {ambition.description !== null && (
              <p className="mt-1 text-sm text-muted">{ambition.description}</p>
            )}
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
              <StatusChip status={ambition.status} openItems={ambition.completed_with_open_items} />
              <span>{countLabel(ambition.goal_count, 'goal')}</span>
              {done !== null && <span>{done}</span>}
              {ambition.target_on !== null && (
                <span>Target {questDateLabel(ambition.target_on)}</span>
              )}
            </p>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="size-3.5" aria-hidden />
            Edit
          </Button>
        </header>

        <CompletionControl kind="ambition" item={ambition} onChanged={refresh} />

        <section aria-labelledby="ambition-goals" className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <h2
              id="ambition-goals"
              className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
            >
              <LevelIcon kind="goal" />
              Goals
            </h2>
            <Button type="button" variant="outline" size="sm" onClick={() => setAddingGoal(true)}>
              <Plus className="size-3.5" aria-hidden />
              Add a goal
            </Button>
          </div>
          {goals.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-line px-4 py-4 text-sm text-muted">
              No goals yet. An ambition can stay a direction, or you can add goals that move it
              forward.
            </p>
          ) : (
            <ul className="grid gap-3 md:grid-cols-2">
              {goals.map((goal, index) => (
                <li key={goal.id}>
                  <GoalCard
                    goal={goal}
                    actions={
                      goals.length > 1 && (
                        <MoveButtons
                          label={goal.title}
                          canUp={index > 0}
                          canDown={index < goals.length - 1}
                          onMove={(direction) => void moveGoal(index, direction)}
                        />
                      )
                    }
                  />
                </li>
              ))}
            </ul>
          )}
          {moveError !== null && (
            <p role="alert" className="text-sm text-bad">
              {moveError}
            </p>
          )}
        </section>

        <section aria-labelledby="ambition-tasks" className="flex flex-col gap-2">
          <h2
            id="ambition-tasks"
            className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
          >
            <LevelIcon kind="task" />
            Tasks directly on this ambition
          </h2>
          <p className="text-xs text-muted">
            Work that serves the ambition without a goal of its own. Each counts toward the ambition
            like a goal does.
          </p>
          <div className="rounded-2xl border border-line bg-surface p-2">
            <TaskList
              tasks={tasks}
              home={{ kind: 'ambition', id: ambition.id }}
              onChanged={refresh}
            />
          </div>
        </section>
      </div>
      <QuestFormDialog
        open={editing}
        onOpenChange={setEditing}
        kind="ambition"
        item={ambition}
        onSaved={refresh}
      />
      <QuestFormDialog
        open={addingGoal}
        onOpenChange={setAddingGoal}
        kind="goal"
        parent={{ kind: 'ambition', id: ambition.id }}
        onSaved={refresh}
      />
    </TaskDrawerProvider>
  )
}
