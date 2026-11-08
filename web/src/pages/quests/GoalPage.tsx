import { EmptyState, PageHeader } from '@/components/PageState'

export function GoalPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Goal" />
      <EmptyState
        title="Coming soon"
        hint="This goal's milestones, chapters, and tasks will show here."
      />
    </div>
  )
}
