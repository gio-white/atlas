import { Pencil } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PageLoading, PageUnavailable } from '@/components/PageState'
import { CompletionControl } from '@/components/quests/CompletionControl'
import { QuestFormDialog } from '@/components/quests/QuestFormDialog'
import { QuestTree } from '@/components/quests/QuestTree'
import { LevelIcon, QuestBreadcrumb, QuestRing, StatusChip } from '@/components/quests/QuestVisuals'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { useQuestView } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import { getSideQuestTree } from '@/lib/api'
import { countLabel, doneTasksLabel, questDateLabel } from '@/lib/quests'

export function SideQuestPage() {
  const id = Number(useParams().id)
  const load = useCallback(() => getSideQuestTree(id), [id])
  const { data, error, reload } = useQuestView(load, "Couldn't load this side quest.")
  const [editing, setEditing] = useState(false)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
  }, [reload])

  if (error !== null && data === null) {
    return <PageUnavailable title="Side quest" message={error} />
  }
  if (data === null || data.side_quest.id !== id) return <PageLoading />

  const { side_quest: quest, chapters, tasks } = data
  const done = doneTasksLabel(quest.done_tasks, quest.total_tasks)

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-6">
        <QuestBreadcrumb
          root={{ label: 'Side quests', to: '/quests/side-quests' }}
          path={[]}
          current={quest.title}
        />
        <header className="flex flex-wrap items-start gap-4">
          <QuestRing value={quest.progress} completed={quest.status === 'completed'} />
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1.5 text-xs font-medium text-iris">
              <LevelIcon kind="side_quest" className="size-3.5" />
              Side quest
            </p>
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{quest.title}</h1>
            {quest.description !== null && (
              <p className="mt-1 text-sm text-muted">{quest.description}</p>
            )}
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
              <StatusChip status={quest.status} openItems={quest.completed_with_open_items} />
              {quest.due_on !== null && <span>Due {questDateLabel(quest.due_on)}</span>}
              {quest.chapter_count > 0 && <span>{countLabel(quest.chapter_count, 'chapter')}</span>}
              {done !== null && <span>{done}</span>}
            </p>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="size-3.5" aria-hidden />
            Edit
          </Button>
        </header>

        <CompletionControl kind="side_quest" item={quest} onChanged={refresh} />

        <section
          aria-label="Chapters and tasks"
          className="rounded-2xl border border-line bg-surface p-3 shadow-[var(--shadow-card)]"
        >
          <QuestTree
            parent={{ kind: 'side_quest', id: quest.id, title: quest.title }}
            chapters={chapters}
            tasks={tasks}
            onChanged={refresh}
          />
        </section>
      </div>
      <QuestFormDialog
        open={editing}
        onOpenChange={setEditing}
        kind="side_quest"
        item={quest}
        onSaved={refresh}
      />
    </TaskDrawerProvider>
  )
}
