import { EmptyState, PageHeader } from '@/components/PageState'

export function SectionPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={title} description={description} homeLink />
      <EmptyState
        title="Nothing here yet"
        hint="This section ships with the matching domain cycle."
      />
    </div>
  )
}
