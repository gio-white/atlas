const MINUTE = 60_000

function clock(date: Date): string {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function localDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()
}

/**
 * "Last updated …" from the newest record's `created_at`, read in local time. Null when no
 * record exists yet, so the caller shows its empty state instead.
 */
export function lastUpdatedLabel(iso: string | null, now: Date = new Date()): string | null {
  if (iso === null) return null
  const at = new Date(iso)
  if (Number.isNaN(at.getTime())) return null
  const ago = now.getTime() - at.getTime()
  if (ago >= 0 && ago < MINUTE) return 'Last updated just now'
  if (ago >= 0 && ago < 60 * MINUTE) return `Last updated ${Math.floor(ago / MINUTE)} min ago`
  const days = Math.round((localDay(now) - localDay(at)) / (24 * 60 * MINUTE))
  if (days === 0) return `Last updated today at ${clock(at)}`
  if (days === 1) return `Last updated yesterday at ${clock(at)}`
  const date = at.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  return `Last updated ${date} at ${clock(at)}`
}
