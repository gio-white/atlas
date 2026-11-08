import { Pencil, Plus } from 'lucide-react'
import { useState } from 'react'

import type { ChapterState, ChapterTree, QuestTask } from '@/lib/api'
import { updateChapter } from '@/lib/api'
import { CHAPTER_STATE_LABELS, doneTasksLabel, KIND_LABELS, shareLabel } from '@/lib/quests'
import { cn } from '@/lib/utils'

import { QuestFormDialog } from './QuestFormDialog'
import { Chip, LevelIcon, QuestBar } from './QuestVisuals'
import { MoveButtons, moveSibling, TaskList } from './TaskList'
import { errorMessage } from './useQuestView'

const STATE_TONE: Record<ChapterState, 'muted' | 'iris' | 'good'> = {
  empty: 'muted',
  not_started: 'muted',
  in_progress: 'iris',
  completed: 'good',
}

export function ChapterStateChip({ state }: { state: ChapterState }) {
  return (
    <Chip
      tone={STATE_TONE[state]}
      className={cn(state === 'empty' && 'border border-dashed border-line bg-transparent')}
    >
      {CHAPTER_STATE_LABELS[state]}
    </Chip>
  )
}

export function ChapterBlock({
  tree,
  parentTitle,
  onChanged,
  onMove,
  canMoveUp,
  canMoveDown,
}: {
  tree: ChapterTree
  parentTitle: string
  onChanged: () => void
  onMove?: (direction: -1 | 1) => void
  canMoveUp: boolean
  canMoveDown: boolean
}) {
  const { chapter, tasks } = tree
  const [editing, setEditing] = useState(false)
  const share = shareLabel(chapter.weight_share)
  const done = doneTasksLabel(chapter.done_tasks, chapter.total_tasks)
  return (
    <section
      aria-label={`Chapter: ${chapter.title}`}
      className="rounded-xl border border-line bg-surface/60 p-2"
      data-testid="chapter"
    >
      <header className="flex flex-wrap items-center gap-2 px-1 pt-1">
        <h4 className="flex min-w-0 flex-1 basis-48 items-center gap-2 text-sm font-semibold break-words text-ink">
          <LevelIcon kind="chapter" label />
          <span className="min-w-0">{chapter.title}</span>
        </h4>
        <div className="ml-auto flex items-center gap-1">
          <ChapterStateChip state={chapter.state} />
          {share !== null && (
            <span
              className="rounded-full bg-raised px-2 py-0.5 text-xs tabular-nums text-muted"
              title={`How much this chapter counts toward ${parentTitle}`}
            >
              <span className="sr-only">Counts </span>
              {share}
            </span>
          )}
          <button
            type="button"
            aria-label={`Edit ${chapter.title}`}
            className="inline-flex size-9 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink"
            onClick={() => setEditing(true)}
          >
            <Pencil className="size-3.5" aria-hidden />
          </button>
          {onMove !== undefined && (
            <MoveButtons
              label={chapter.title}
              canUp={canMoveUp}
              canDown={canMoveDown}
              onMove={onMove}
            />
          )}
        </div>
      </header>
      {chapter.state !== 'empty' && (
        <div className="flex items-center gap-2 px-1 pt-1 pb-1">
          <QuestBar
            value={chapter.progress}
            completed={chapter.state === 'completed'}
            className="flex-1"
          />
          {done !== null && <span className="text-xs text-muted tabular-nums">{done}</span>}
        </div>
      )}
      <TaskList
        tasks={tasks}
        home={{ kind: 'chapter', id: chapter.id }}
        onChanged={onChanged}
        emptyHint="No tasks yet. An empty chapter never counts as done."
        compact
      />
      <QuestFormDialog
        open={editing}
        onOpenChange={setEditing}
        kind="chapter"
        item={chapter}
        parentTitle={parentTitle}
        onSaved={onChanged}
      />
    </section>
  )
}

/**
 * The inside of a milestone or a side quest: its chapters (each with its tasks), then the
 * tasks directly on it, with add controls at every level.
 */
export function QuestTree({
  parent,
  chapters,
  tasks,
  onChanged,
}: {
  parent: { kind: 'milestone' | 'side_quest'; id: number; title: string }
  chapters: ChapterTree[]
  tasks: QuestTask[]
  onChanged: () => void
}) {
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const level = KIND_LABELS[parent.kind].toLowerCase()

  async function moveChapter(index: number, direction: -1 | 1) {
    setError(null)
    try {
      await moveSibling(
        chapters.map((tree) => tree.chapter),
        index,
        direction,
        (id, position) => updateChapter(id, { position }),
      )
    } catch (caught) {
      setError(errorMessage(caught, "Couldn't reorder the chapters."))
    } finally {
      onChanged()
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {chapters.length === 0 && tasks.length === 0 && (
        <p className="text-sm text-muted">
          Nothing here yet. Add a chapter for a batch of work, or add tasks directly.
        </p>
      )}
      {chapters.length > 0 && (
        <div className="flex flex-col gap-2">
          {chapters.map((tree, index) => (
            <ChapterBlock
              key={tree.chapter.id}
              tree={tree}
              parentTitle={parent.title}
              onChanged={onChanged}
              onMove={chapters.length > 1 ? (dir) => void moveChapter(index, dir) : undefined}
              canMoveUp={index > 0}
              canMoveDown={index < chapters.length - 1}
            />
          ))}
        </div>
      )}
      {error !== null && (
        <p role="alert" className="text-sm text-bad">
          {error}
        </p>
      )}
      <div className="flex flex-col gap-1">
        {chapters.length > 0 && tasks.length > 0 && (
          <h4 className="px-2 pt-1 text-xs font-medium text-muted">
            Tasks directly on this {level}
          </h4>
        )}
        <TaskList
          tasks={tasks}
          home={{ kind: parent.kind, id: parent.id }}
          onChanged={onChanged}
          compact
        />
      </div>
      <button
        type="button"
        className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg px-2 text-sm text-muted hover:bg-raised hover:text-ink"
        onClick={() => setAdding(true)}
      >
        <Plus className="size-4" aria-hidden />
        <LevelIcon kind="chapter" className="size-3.5" />
        Add a chapter
      </button>
      <QuestFormDialog
        open={adding}
        onOpenChange={setAdding}
        kind="chapter"
        parent={{ kind: parent.kind, id: parent.id }}
        onSaved={onChanged}
      />
    </div>
  )
}
