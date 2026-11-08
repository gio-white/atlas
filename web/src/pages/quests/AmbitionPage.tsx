import { EmptyState, PageHeader } from '@/components/PageState'

export function AmbitionPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Ambition" />
      <EmptyState title="Coming soon" hint="This ambition's goals and tasks will show here." />
    </div>
  )
}
