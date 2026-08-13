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
