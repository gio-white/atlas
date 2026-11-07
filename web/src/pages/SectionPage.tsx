import { EmptyState, PageHeader } from '@/components/PageState'

export function SectionPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={title} description={description} homeLink />
      <EmptyState title="Coming soon" hint="There is nothing to show on this page yet." />
    </div>
  )
}
