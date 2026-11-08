import { EmptyState, PageHeader } from '@/components/PageState'

export function InboxPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Inbox" description="Things you wrote down but haven't sorted yet." />
      <EmptyState
        title="Coming soon"
        hint="Capture an idea here, then move it into a quest when you're ready."
      />
    </div>
  )
}
