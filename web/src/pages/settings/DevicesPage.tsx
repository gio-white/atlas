import { PageHeader } from '@/components/PageState'
import { DataSourcesSettings } from '@/components/settings/DataSourcesSettings'

/** Settings → Devices: the names of the phones and computers screen time comes from. */
export function DevicesPage() {
  return (
    <div className="flex max-w-xl flex-col gap-5">
      <PageHeader
        tab
        title="Devices"
        description="The phones and computers your data comes from."
      />
      <DataSourcesSettings />
    </div>
  )
}
