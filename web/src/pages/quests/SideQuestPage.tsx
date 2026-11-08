import { EmptyState, PageHeader } from '@/components/PageState'

export function SideQuestPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Side quest" />
      <EmptyState title="Coming soon" hint="This side quest's chapters and tasks will show here." />
    </div>
  )
}
