import { ChevronDown, Diamond, Pencil, Plus } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PageLoading, PageUnavailable } from '@/components/PageState'
import { CompletionControl } from '@/components/quests/CompletionControl'
import { QuestFormDialog } from '@/components/quests/QuestFormDialog'
import { QuestTree } from '@/components/quests/QuestTree'
import {
  LevelIcon,
  QuestBar,
  QuestBreadcrumb,
  QuestRing,
  StatusChip,
} from '@/components/quests/QuestVisuals'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { MoveButtons, moveSibling, TaskList } from '@/components/quests/TaskList'
import { errorMessage, useQuestView } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import { getGoalTree, type MilestoneTree, updateMilestone } from '@/lib/api'
import { countLabel, doneTasksLabel, progressLabel, questDateLabel, shareLabel } from '@/lib/quests'
import { cn } from '@/lib/utils'

export function GoalPage() {
  const id = Number(useParams().id)
  const load = useCallback(() => getGoalTree(id), [id])
  const { data, error, reload } = useQuestView(load, "Couldn't load this goal.")
  const [editing, setEditing] = useState(false)
  const [addingMilestone, setAddingMilestone] = useState(false)
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set())
  const [moveError, setMoveError] = useState<string | null>(null)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
  }, [reload])

  // Completed milestones start folded; open ones start expanded.
  const completedIds = data?.milestones
    .filter((tree) => tree.milestone.status === 'completed')
    .map((tree) => tree.milestone.id)
    .join(',')
  useEffect(() => {
    setCollapsed(new Set((completedIds ?? '').split(',').filter(Boolean).map(Number)))
  }, [completedIds])

  if (error !== null && data === null) {
    return <PageUnavailable title="Goal" message={error} />
  }
  if (data === null || data.goal.id !== id) return <PageLoading />

  const { goal, milestones, tasks } = data
  const done = doneTasksLabel(goal.done_tasks, goal.total_tasks)

  function toggle(milestoneId: number) {
    setCollapsed((current) => {
      const next = new Set(current)
      if (next.has(milestoneId)) next.delete(milestoneId)
      else next.add(milestoneId)
      return next
    })
  }

  async function moveMilestone(index: number, direction: -1 | 1) {
    setMoveError(null)
    try {
      await moveSibling(
        milestones.map((tree) => tree.milestone),
        index,
        direction,
        (milestoneId, position) => updateMilestone(milestoneId, { position }),
      )
    } catch (caught) {
      setMoveError(errorMessage(caught, "Couldn't reorder the milestones."))
    } finally {
      refresh()
    }
  }

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-6">
        <QuestBreadcrumb
          root={{ label: 'Main quests', to: '/quests' }}
          path={goal.path}
          current={goal.title}
        />
        <header className="flex flex-wrap items-start gap-4">
          <QuestRing value={goal.progress} completed={goal.status === 'completed'} size={64} />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 text-xs font-medium text-accent">
              <LevelIcon kind="goal" className="size-3.5" />
              Goal
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{goal.title}</h1>
            {goal.description !== null && (
              <p className="mt-1 text-sm text-muted">{goal.description}</p>
            )}
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
              <StatusChip status={goal.status} openItems={goal.completed_with_open_items} />
              {goal.due_on !== null && <span>Due {questDateLabel(goal.due_on)}</span>}
              <span>{countLabel(goal.milestone_count, 'milestone')}</span>
              {done !== null && <span>{done}</span>}
            </p>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="size-3.5" aria-hidden />
            Edit
          </Button>
        </header>

        {goal.success_description !== null && (
          <section
            aria-label="What success looks like"
            className="rounded-2xl border border-accent/25 bg-accent/6 px-4 py-3"
          >
            <p className="text-xs font-medium text-accent">What success looks like</p>
            <p className="mt-1 font-serif text-[15px] text-ink">{goal.success_description}</p>
          </section>
        )}

        <CompletionControl kind="goal" item={goal} onChanged={refresh} />

        <section aria-labelledby="quest-map" className="flex flex-col gap-3">
          <div>
            <h2 id="quest-map" className="text-lg font-semibold tracking-tight text-ink">
              Quest map
            </h2>
            <p className="text-xs text-muted">
              Finishing a task fills its chapter, chapters and tasks fill their milestone, and
              milestones and tasks fill this goal. The percentage beside an item is how much it
              counts toward the level above it.
            </p>
          </div>
          <ol className="relative flex flex-col gap-4 pl-9 sm:pl-10" aria-label="Milestones">
            <span
              aria-hidden
              className="absolute top-3 bottom-3 left-[15px] w-px border-l-2 border-dashed border-line"
            />
            {milestones.map((tree, index) => (
              <MilestoneNode
                key={tree.milestone.id}
                tree={tree}
                goalTitle={goal.title}
                expanded={!collapsed.has(tree.milestone.id)}
                onToggle={() => toggle(tree.milestone.id)}
                onChanged={refresh}
                onMove={milestones.length > 1 ? (dir) => void moveMilestone(index, dir) : undefined}
                canMoveUp={index > 0}
                canMoveDown={index < milestones.length - 1}
              />
            ))}
            <li className="relative">
              <span
                aria-hidden
                className="absolute top-1 -left-9 inline-flex size-8 sm:-left-10 items-center justify-center rounded-full border-2 border-dashed border-line bg-canvas text-muted"
              >
                <Plus className="size-3.5" />
              </span>
              <button
                type="button"
                className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm text-muted hover:bg-raised hover:text-ink"
                onClick={() => setAddingMilestone(true)}
              >
                <Diamond className="size-3.5 text-accent" aria-hidden />
                {milestones.length === 0 ? 'Add the first milestone' : 'Add a milestone'}
              </button>
            </li>
          </ol>
          {moveError !== null && (
            <p role="alert" className="text-sm text-bad">
              {moveError}
            </p>
          )}
        </section>

        <section aria-labelledby="goal-tasks" className="flex flex-col gap-2">
          <h2
            id="goal-tasks"
            className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
          >
            <LevelIcon kind="task" />
            Tasks directly on this goal
          </h2>
          <p className="text-xs text-muted">
            Work that moves the goal without a milestone. Each counts toward the goal beside the
            milestones.
          </p>
          <div className="rounded-2xl border border-line bg-surface p-2">
            <TaskList tasks={tasks} home={{ kind: 'goal', id: goal.id }} onChanged={refresh} />
          </div>
        </section>
      </div>
      <QuestFormDialog
        open={editing}
        onOpenChange={setEditing}
        kind="goal"
        item={goal}
        parentTitle={goal.path.at(-1)?.title}
        onSaved={refresh}
      />
      <QuestFormDialog
        open={addingMilestone}
        onOpenChange={setAddingMilestone}
        kind="milestone"
        parent={{ kind: 'goal', id: goal.id }}
        onSaved={refresh}
      />
    </TaskDrawerProvider>
  )
}

function MilestoneNode({
  tree,
  goalTitle,
  expanded,
  onToggle,
  onChanged,
  onMove,
  canMoveUp,
  canMoveDown,
}: {
  tree: MilestoneTree
  goalTitle: string
  expanded: boolean
  onToggle: () => void
  onChanged: () => void
  onMove?: (direction: -1 | 1) => void
  canMoveUp: boolean
  canMoveDown: boolean
}) {
  const { milestone, chapters, tasks } = tree
  const [editing, setEditing] = useState(false)
  const completed = milestone.status === 'completed'
  const share = shareLabel(milestone.weight_share)
  const done = doneTasksLabel(milestone.done_tasks, milestone.total_tasks)
  const bodyId = `milestone-${milestone.id}-body`
  return (
    <li className="relative" data-testid="milestone">
      <span
        aria-hidden
        className={cn(
          'absolute top-2 -left-9 inline-flex size-8 sm:-left-10 items-center justify-center',
          completed ? 'text-good' : 'text-accent',
        )}
      >
        <Diamond
          className={cn('size-7', completed ? 'fill-good/25' : 'fill-canvas')}
          strokeWidth={2}
        />
      </span>
      <div
        className={cn(
          'rounded-2xl border bg-surface shadow-[var(--shadow-card)]',
          completed ? 'border-good/30' : 'border-line',
        )}
      >
        <div className="flex flex-wrap items-start gap-2 p-3">
          <button
            type="button"
            aria-expanded={expanded}
            aria-controls={bodyId}
            className="flex min-h-10 min-w-0 flex-1 basis-56 items-start gap-2 rounded-lg text-left"
            onClick={onToggle}
          >
            <ChevronDown
              className={cn(
                'mt-1 size-4 shrink-0 text-muted motion-safe:transition-transform',
                !expanded && '-rotate-90',
              )}
              aria-hidden
            />
            <span className="min-w-0 flex-1">
              <span className="sr-only">Milestone: </span>
              <span className="block font-semibold tracking-tight text-ink">{milestone.title}</span>
              <span className="mt-0.5 block text-xs text-muted">
                {[
                  milestone.progress === null ? 'Not broken down yet' : null,
                  done,
                  milestone.due_on === null ? null : `Due ${questDateLabel(milestone.due_on)}`,
                  milestone.chapter_count > 0
                    ? countLabel(milestone.chapter_count, 'chapter')
                    : null,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </span>
            </span>
          </button>
          <div className="ml-auto flex flex-wrap items-center justify-end gap-1">
            {milestone.status !== 'active' && (
              <StatusChip
                status={milestone.status}
                openItems={milestone.completed_with_open_items}
              />
            )}
            {share !== null && (
              <span
                className="rounded-full bg-accent/10 px-2 py-0.5 text-xs font-medium tabular-nums text-accent"
                title={`How much this milestone counts toward ${goalTitle}`}
              >
                <span className="sr-only">Counts </span>
                {share}
              </span>
            )}
            <button
              type="button"
              aria-label={`Edit ${milestone.title}`}
              className="inline-flex size-9 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink"
              onClick={() => setEditing(true)}
            >
              <Pencil className="size-3.5" aria-hidden />
            </button>
            {onMove !== undefined && (
              <MoveButtons
                label={milestone.title}
                canUp={canMoveUp}
                canDown={canMoveDown}
                onMove={onMove}
              />
            )}
          </div>
        </div>
        {milestone.progress !== null && (
          <div className="flex items-center gap-2 px-3 pb-3">
            <QuestBar value={milestone.progress} completed={completed} className="flex-1" />
            <span className="text-xs tabular-nums text-muted">
              {progressLabel(milestone.progress)}
            </span>
          </div>
        )}
        {expanded && (
          <div id={bodyId} className="flex flex-col gap-3 border-t border-line p-2 sm:p-3">
            <QuestTree
              parent={{ kind: 'milestone', id: milestone.id, title: milestone.title }}
              chapters={chapters}
              tasks={tasks}
              onChanged={onChanged}
            />
            <CompletionControl kind="milestone" item={milestone} onChanged={onChanged} compact />
          </div>
        )}
      </div>
      <QuestFormDialog
        open={editing}
        onOpenChange={setEditing}
        kind="milestone"
        item={milestone}
        parentTitle={goalTitle}
        onSaved={onChanged}
      />
    </li>
  )
}
