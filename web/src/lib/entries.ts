import type { Entry, EntryCreate, Metric } from './api'
import { shiftPeriodDate } from './dates'
import { formatEntryValue } from './format'
import { parseLogValue, rawFromEntry } from './value'

export type EntryDay = { day: string; entries: Entry[] }

export type EntryDraft = { raw: string; boolValue: boolean; occurredOn: string; note: string }

export const HISTORY_DAYS = 30

export function historyRange(asOf: string, days = HISTORY_DAYS): { start: string; end: string } {
  let start = asOf
  for (let step = 1; step < days; step += 1) start = shiftPeriodDate(start, 'day', -1)
  return { start, end: asOf }
}

/** Groups entries that arrive newest first into one block per day, keeping that order. */
export function groupEntriesByDay(entries: Entry[]): EntryDay[] {
  const days: EntryDay[] = []
  for (const entry of entries) {
    const last = days.at(-1)
    if (last !== undefined && last.day === entry.occurred_on) last.entries.push(entry)
    else days.push({ day: entry.occurred_on, entries: [entry] })
  }
  return days
}

export function entryValueLabel(entry: Entry, metric: Metric | undefined): string {
  const value = formatEntryValue(entry.value_num, entry.value_bool, entry.value_text)
  if (entry.value_num === null || metric?.unit == null) return value
  return `${value} ${metric.unit}`
}

export function draftFromEntry(entry: Entry): EntryDraft {
  return {
    raw: rawFromEntry(entry.value_num, entry.value_bool, entry.value_text),
    boolValue: entry.value_bool ?? true,
    occurredOn: entry.occurred_on,
    note: entry.note ?? '',
  }
}

/**
 * The PATCH body for what the draft changed. Value is left out when the metric is unknown
 * (archived and not loaded), so a correction can still fix the date or note.
 */
export function amendBodyFromDraft(
  entry: Entry,
  metric: Metric | undefined,
  draft: EntryDraft,
): Partial<Pick<EntryCreate, 'value' | 'occurred_on' | 'note'>> {
  const body: Partial<Pick<EntryCreate, 'value' | 'occurred_on' | 'note'>> = {}
  if (metric !== undefined) {
    const before = draftFromEntry(entry)
    const changed =
      metric.value_type === 'bool' ? draft.boolValue !== before.boolValue : draft.raw !== before.raw
    if (changed) body.value = parseLogValue(metric.value_type, draft.raw, draft.boolValue)
  }
  if (draft.occurredOn !== entry.occurred_on) body.occurred_on = draft.occurredOn
  const note = draft.note.trim() === '' ? null : draft.note.trim()
  if (note !== entry.note) body.note = note
  return body
}
