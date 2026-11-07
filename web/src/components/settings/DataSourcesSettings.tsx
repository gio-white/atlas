import { useCallback, useEffect, useState } from 'react'

import { slugFromName, TaxonomyCard } from '@/components/settings/ScreenTimeSettings'
import { ApiError, createScreenDevice, listScreenDevices, type ScreenDevice } from '@/lib/api'

/**
 * Devices that screen time is recorded from. Self-contained so it can move into a Settings
 * page as one line; `onChanged` lets a host page refresh what it displays.
 */
export function DataSourcesSettings({ onChanged }: { onChanged?: () => Promise<void> }) {
  const [devices, setDevices] = useState<ScreenDevice[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => setDevices(await listScreenDevices()), [])

  useEffect(() => {
    load().catch((caught: unknown) =>
      setError(caught instanceof ApiError ? caught.message : 'Could not load devices'),
    )
  }, [load])

  if (devices === null) return <p className="text-sm text-muted">{error ?? 'Loading…'}</p>

  return (
    <TaxonomyCard
      title="Devices"
      description="Where screen time is recorded from"
      noun="device"
      onCreate={async (name) => {
        await createScreenDevice({ slug: slugFromName(name), name })
        await Promise.all([load(), onChanged?.()])
      }}
      rows={devices.map((device) => (
        <li key={device.slug} className="text-ink">
          {device.name}
        </li>
      ))}
    />
  )
}
