import type { Comparator, PaceStatus } from './api'

export function formatComparator(comparator: Comparator): string {
  if (comparator === 'at_least') return '≥'
  if (comparator === 'at_most') return '≤'
  return '='
}

export function formatPace(pace: PaceStatus): string {
  return pace.replaceAll('_', ' ')
}

export function formatEntryValue(
  valueNum: number | null,
  valueBool: boolean | null,
  valueText: string | null,
): string {
  if (valueBool !== null) return valueBool ? 'yes' : 'no'
  if (valueText !== null) return valueText
  if (valueNum !== null) return String(valueNum)
  return '—'
}

export function formatPercent(fraction: number | null): string {
  if (fraction === null) return '—'
  return `${Math.round(fraction * 100)}%`
}

export function formatMinutes(minutes: number | null): string {
  if (minutes === null) return '—'
  const total = Math.max(0, Math.round(minutes))
  const hours = Math.floor(total / 60)
  const mins = total % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

export function formatDeltaFraction(fraction: number | null): string | null {
  if (fraction === null) return null
  const pct = Math.round(Math.abs(fraction) * 100)
  const arrow = fraction < 0 ? '↓' : '↑'
  return `${arrow} ${pct}%`
}
