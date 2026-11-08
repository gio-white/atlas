import { EmptyState, PageHeader } from '@/components/PageState'

export function SideQuestsPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Side quests"
        description="Things to get done that aren't part of a goal."
      />
      <EmptyState
        title="Coming soon"
        hint="Your side quests and standalone tasks will show here."
      />
    </div>
  )
}
