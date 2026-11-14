import { ArrowRight, CalendarDays, Plus } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import type { QuestGoal, QuestTask, SideQuest } from '@/lib/api'
import { countLabel, doneTasksLabel, questDateLabel } from '@/lib/quests'
import { cn } from '@/lib/utils'

import { LevelIcon, QuestRing, StatusChip } from './QuestVisuals'
import { useOpenTask } from './TaskDrawer'

type CardItem = {
  id: number
  title: string
  description: string | null
  status: QuestGoal['status']
  progress: number | null
  completed_with_open_items: boolean
  done_tasks: number
  total_tasks: number
  next_action: QuestTask | null
}

function NextAction({ task, href, done }: { task: QuestTask | null; href: string; done: boolean }) {
  const openTask = useOpenTask()
  if (done) return null
  if (task === null) {
    return (
      <Link
        to={href}
        className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm text-muted hover:bg-raised hover:text-ink"
      >
        <Plus className="size-4" aria-hidden />
        Add a task
      </Link>
    )
  }
  return (
    <button
      type="button"
      className="flex min-h-10 w-full items-center gap-2 rounded-lg bg-accent/8 px-3 py-2 text-left hover:bg-accent/14"
      onClick={() => openTask(task.id)}
    >
      <span className="text-xs font-medium text-accent">Next</span>
      <span className="min-w-0 flex-1 truncate text-sm text-ink">{task.title}</span>
      <ArrowRight className="size-3.5 shrink-0 text-accent" aria-hidden />
    </button>
  )
}

function CardShell({
  kind,
  item,
  href,
  date,
  counts,
  compact = false,
  actions,
}: {
  kind: 'goal' | 'side_quest'
  item: CardItem
  href: string
  date: string | null
  counts: string[]
  compact?: boolean
  actions?: ReactNode
}) {
  const completed = item.status === 'completed'
  const done = doneTasksLabel(item.done_tasks, item.total_tasks)
  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]',
        completed && 'bg-surface/70',
      )}
      aria-label={item.title}
    >
      <div className="flex items-start gap-3">
        <QuestRing value={item.progress} completed={completed} size={compact ? 44 : 56} />
        <div className="min-w-0 flex-1">
          <h3 className="flex items-start gap-1.5 font-semibold tracking-tight text-ink">
            <LevelIcon kind={kind} className="mt-1 size-3.5" label />
            <Link to={href} className="min-w-0 hover:underline">
              {item.title}
            </Link>
          </h3>
          {item.description !== null && !compact && (
            <p className="mt-0.5 line-clamp-2 text-sm text-muted">{item.description}</p>
          )}
          {item.progress === null && (
            <p className="mt-0.5 text-xs text-muted">Not broken down yet</p>
          )}
        </div>
        {actions}
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
        <StatusChip status={item.status} openItems={item.completed_with_open_items} />
        {date !== null && (
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="size-3" aria-hidden />
            {date}
          </span>
        )}
        {[...counts, ...(done === null ? [] : [done])].map((text) => (
          <span key={text}>{text}</span>
        ))}
      </div>
      <NextAction task={item.next_action} href={href} done={completed} />
    </article>
  )
}

export function GoalCard({ goal, actions }: { goal: QuestGoal; actions?: ReactNode }) {
  return (
    <CardShell
      actions={actions}
      kind="goal"
      item={goal}
      href={`/quests/goals/${goal.id}`}
      date={goal.due_on === null ? null : `Due ${questDateLabel(goal.due_on)}`}
      counts={[countLabel(goal.milestone_count, 'milestone')]}
    />
  )
}

export function SideQuestCard({ quest }: { quest: SideQuest }) {
  return (
    <CardShell
      kind="side_quest"
      item={quest}
      href={`/quests/side-quests/${quest.id}`}
      date={quest.due_on === null ? null : `Due ${questDateLabel(quest.due_on)}`}
      counts={quest.chapter_count > 0 ? [countLabel(quest.chapter_count, 'chapter')] : []}
      compact
    />
  )
}
