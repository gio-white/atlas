import { EmptyState, PageHeader } from '@/components/PageState'

/** Stats → Health. It only ever shows device data, and none arrives yet. */
export function HealthPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader tab title="Health" />
      <EmptyState title="No health data yet" hint="This fills in once a device is connected." />
    </div>
  )
}
