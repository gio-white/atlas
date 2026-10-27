import type { Period, ScreenBudget, ScreenSessionRecord } from './api'
import { toLocalInput } from './dates'
import { formatComparator, formatMinutes } from './format'

const PERIOD_PHRASE: Record<Period, string> = { day: 'a day', week: 'a week', month: 'a month' }

export function budgetSlug(targetSlug: string, period: Period): string {
  return `${targetSlug}-${period}-cap`
}

export function budgetSummary(
  budget: Pick<ScreenBudget, 'comparator' | 'target_value' | 'period'>,
) {
  return `${formatComparator(budget.comparator)} ${formatMinutes(budget.target_value)} ${PERIOD_PHRASE[budget.period]}`
}

export type BudgetState = { label: string; open: boolean; counting: boolean }

/**
 * `active_to` is inclusive, so a cap ended today still counts today ("last day"). `open` is
 * whether it has no end date yet, which decides between End and Resume.
 */
export function budgetState(
  budget: Pick<ScreenBudget, 'active_from' | 'active_to'>,
  asOf: string,
): BudgetState {
  if (budget.active_from > asOf) {
    return {
      label: `starts ${budget.active_from}`,
      open: budget.active_to === null,
      counting: false,
    }
  }
  if (budget.active_to === null) return { label: 'active', open: true, counting: true }
  if (budget.active_to < asOf)
    return { label: `ended ${budget.active_to}`, open: false, counting: false }
  return { label: `last day ${budget.active_to}`, open: false, counting: true }
}

export function sessionTimeLabel(record: ScreenSessionRecord): string {
  if (record.started_at === null || record.ended_at === null) return 'duration only'
  const start = toLocalInput(record.started_at).slice(11)
  const end = toLocalInput(record.ended_at).slice(11)
  return `${start}–${end}`
}

export type SessionDraft = {
  started: string
  ended: string
  minutes: string
  device: string
  note: string
}

export function draftFromSession(record: ScreenSessionRecord): SessionDraft {
  return {
    started: record.started_at === null ? '' : toLocalInput(record.started_at),
    ended: record.ended_at === null ? '' : toLocalInput(record.ended_at),
    minutes: String(record.minutes),
    device: record.device ?? '',
    note: record.note ?? '',
  }
}

/**
 * The PATCH body for a session edit. An interval session sends both ends together (the
 * server re-derives minutes); a duration-only session sends minutes. Unchanged fields stay out.
 */
export function sessionUpdateBody(record: ScreenSessionRecord, draft: SessionDraft) {
  const before = draftFromSession(record)
  const body: {
    started_at?: string
    ended_at?: string
    minutes?: number
    device?: string | null
    note?: string | null
  } = {}
  if (record.started_at !== null) {
    if (draft.started !== before.started || draft.ended !== before.ended) {
      if (draft.started === '' || draft.ended === '') throw new Error('start and end are required')
      body.started_at = new Date(draft.started).toISOString()
      body.ended_at = new Date(draft.ended).toISOString()
    }
  } else if (draft.minutes !== before.minutes) {
    const minutes = Number(draft.minutes)
    if (Number.isNaN(minutes) || minutes <= 0) throw new Error('minutes must be above 0')
    body.minutes = minutes
  }
  if (draft.device !== before.device) body.device = draft.device === '' ? null : draft.device
  const note = draft.note.trim() === '' ? null : draft.note.trim()
  if (note !== record.note) body.note = note
  return body
}
