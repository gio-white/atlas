import type { HabitWeekProgress } from './api'
import { shortDateLabel, weekdayLabel } from './dates'
import { formatMinutes } from './format'
import { formatAmount } from './habits'
import { addDays, weekLabel, weekStart } from './timeBlocks'

/** "This week" for the week holding today, otherwise "Week of 9 Nov 2026". */
export function weekTitle(monday: string, today: string): string {
  if (monday === weekStart(today)) return 'This week'
  const label = new Date(`${monday}T00:00:00`).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
  return `Week of ${label}`
}

/** "9–15 Nov 2026", then "· up to Thu 12 Nov" while the week is counted only in part. */
export function weekRangeLine(monday: string, asOf: string, complete: boolean): string {
  const range = weekLabel(monday)
  if (complete) return range
  return `${range} · up to ${weekdayLabel(asOf)} ${shortDateLabel(asOf)}`
}

/**
 * The `?on=` dates for the previous and next week: each week's Sunday, so the whole week is
 * counted, and null for the week holding today (no `?on=` at all). `next` is undefined when
 * there is no next week to show yet.
 */
export function weekSteps(
  monday: string,
  today: string,
): { previous: string | null; next: string | null | undefined } {
  const thisMonday = weekStart(today)
  const previousSunday = addDays(monday, -1)
  const nextSunday = addDays(monday, 13)
  return {
    previous: weekStart(previousSunday) === thisMonday ? null : previousSunday,
    next:
      monday >= thisMonday ? undefined : weekStart(nextSunday) === thisMonday ? null : nextSunday,
  }
}

const VS = 'vs last week'

function signed(value: number, text: string): string {
  return `${value > 0 ? '+' : '−'}${text}`
}

/** "+35m vs last week"; null when either week has no number. */
export function minutesChange(current: number | null, previous: number | null): string | null {
  if (current === null || previous === null) return null
  const delta = Math.round(current - previous)
  if (delta === 0) return `Same as last week`
  return `${signed(delta, formatMinutes(Math.abs(delta)))} ${VS}`
}

/** "+2 vs last week" for counts and scores. */
export function countChange(current: number | null, previous: number | null): string | null {
  if (current === null || previous === null) return null
  const delta = Math.round(current - previous)
  if (delta === 0) return `Same as last week`
  return `${signed(delta, String(Math.abs(delta)))} ${VS}`
}

/** "+5 points vs last week" for a share shown as a percentage. */
export function shareChange(current: number | null, previous: number | null): string | null {
  if (current === null || previous === null) return null
  const delta = Math.round((current - previous) * 100)
  if (delta === 0) return `Same as last week`
  const points = Math.abs(delta) === 1 ? 'point' : 'points'
  return `${signed(delta, `${Math.abs(delta)} ${points}`)} ${VS}`
}

/** "20m later than last week" for a time of day. */
export function clockChange(current: number | null, previous: number | null): string | null {
  if (current === null || previous === null) return null
  const delta = Math.round(current - previous)
  if (delta === 0) return `Same as last week`
  return `${formatMinutes(Math.abs(delta))} ${delta > 0 ? 'later' : 'earlier'} than last week`
}

/**
 * One habit's line for the week. Daily habits count the days judged so far ("5 of 6 days");
 * weekly and monthly ones show their amount for the period ("1 of 3", "2 of 4 this month").
 */
export function habitWeekLabel(row: HabitWeekProgress): string {
  if (row.period === 'day') {
    if (row.judged === 0) return 'No full days yet'
    const days = row.judged === 1 ? 'day' : 'days'
    return row.kind === 'quit'
      ? `${row.kept} of ${row.judged} ${days} clean`
      : `${row.kept} of ${row.judged} ${days}`
  }
  if (row.target === null) return 'On a break'
  const amount = `${formatAmount(row.value, row.kind, row.unit)} of ${formatAmount(row.target, row.kind, row.unit)}`
  return row.period === 'month' ? `${amount} this month` : amount
}
