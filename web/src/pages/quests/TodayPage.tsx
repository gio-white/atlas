import { EmptyState, PageHeader } from '@/components/PageState'

export function TodayPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Today" description="Your sessions and next steps for today." />
      <EmptyState
        title="Coming soon"
        hint="Today's time blocks and what to do next will show here."
      />
    </div>
  )
}
