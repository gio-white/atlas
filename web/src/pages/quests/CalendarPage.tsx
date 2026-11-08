import { EmptyState, PageHeader } from '@/components/PageState'

export function CalendarPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Calendar" description="When you plan to work on your tasks." />
      <EmptyState title="Coming soon" hint="Your week of time blocks will show here." />
    </div>
  )
}
