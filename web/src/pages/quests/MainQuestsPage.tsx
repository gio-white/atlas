import { EmptyState, PageHeader } from '@/components/PageState'

export function MainQuestsPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Main quests"
        description="Your ambitions and the goals that move them forward."
      />
      <EmptyState title="Coming soon" hint="Your ambitions and goals will show here." />
    </div>
  )
}
