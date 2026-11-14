import { Plus } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { SideQuestCard } from '@/components/quests/QuestCard'
import { QuestFormDialog } from '@/components/quests/QuestFormDialog'
import { LevelIcon } from '@/components/quests/QuestVisuals'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { TaskList } from '@/components/quests/TaskList'
import { useQuestView } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import { getSideQuestsView } from '@/lib/api'

export function SideQuestsPage() {
  const { data, error, reload } = useQuestView(getSideQuestsView, "Couldn't load your side quests.")
  const [creating, setCreating] = useState(false)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
  }, [reload])

  if (error !== null && data === null) {
    return <PageUnavailable tab title="Side quests" message={error} />
  }
  if (data === null) return <PageLoading />

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <PageHeader
            tab
            title="Side quests"
            description="Work that matters but isn't part of a goal."
          />
          <Button
            type="button"
            className="bg-accent hover:bg-accent/90"
            onClick={() => setCreating(true)}
          >
            <Plus className="size-4" aria-hidden />
            New side quest
          </Button>
        </div>

        <section aria-labelledby="structured-side-quests" className="flex flex-col gap-3">
          <h2
            id="structured-side-quests"
            className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
          >
            <LevelIcon kind="side_quest" />
            Side quests
          </h2>
          {data.side_quests.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-line px-4 py-4 text-sm text-muted">
              No side quests yet. Create one for bigger work with its own chapters, like a tax
              declaration or a move.
            </p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {data.side_quests.map((quest) => (
                <SideQuestCard key={quest.id} quest={quest} />
              ))}
            </div>
          )}
        </section>

        <section aria-labelledby="standalone-tasks" className="flex flex-col gap-2">
          <h2
            id="standalone-tasks"
            className="flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
          >
            <LevelIcon kind="task" />
            Standalone tasks
          </h2>
          <p className="text-xs text-muted">One-off things that stand on their own.</p>
          <div className="rounded-2xl border border-line bg-surface p-2">
            <TaskList
              tasks={data.standalone_tasks}
              home="standalone"
              onChanged={refresh}
              showShare={false}
              emptyHint="No standalone tasks."
            />
          </div>
        </section>
      </div>
      <QuestFormDialog
        open={creating}
        onOpenChange={setCreating}
        kind="side_quest"
        onSaved={refresh}
      />
    </TaskDrawerProvider>
  )
}
