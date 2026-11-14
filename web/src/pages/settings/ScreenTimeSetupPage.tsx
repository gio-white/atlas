import { PageHeader } from '@/components/PageState'
import { ScreenTimeSettings } from '@/components/settings/ScreenTimeSettings'

/** Settings → Screen time setup: configuration only. The data itself is on Stats → Screen time. */
export function ScreenTimeSetupPage() {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        tab
        title="Screen time setup"
        description="Which categories count as Good or Bad, the category of each app, and daily caps."
      />
      <ScreenTimeSettings />
    </div>
  )
}
