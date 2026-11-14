// Display helpers for time blocks (docs/domain/time-blocks.md#screens). The API stores and
// returns UTC instants; the screens show and edit browser-local dates and times. Every
// local ↔ UTC conversion goes through `localToUtc` / `utcToLocal` here. Nothing in this file
// decides a block's state: unconfirmed, overlaps, and planned effort come from the API.

import type { ItemRef, TaskStatus, TimeBlockStatus } from '@/lib/api'
import { formatMinutes } from '@/lib/format'

export type LocalParts = { date: string; time: string }

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

function isoDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function localDate(date: string, time = '00:00'): Date {
  const [year, month, day] = date.split('-').map(Number)
  const [hours, minutes] = time.split(':').map(Number)
  return new Date(year, month - 1, day, hours, minutes)
}

/** A local date (`YYYY-MM-DD`) and time (`HH:mm`) → the UTC instant the API stores. */
export function localToUtc(date: string, time: string): string {
  return localDate(date, time).toISOString()
}

/** A UTC instant from the API → the local date and time inputs show. */
export function utcToLocal(iso: string): LocalParts {
  const value = new Date(iso)
  return { date: isoDate(value), time: `${pad(value.getHours())}:${pad(value.getMinutes())}` }
}

/** "09:05", 24-hour, local time. */
export function formatTime(iso: string): string {
  return utcToLocal(iso).time
}

/** "09:00–10:30" in local time. */
export function formatTimeRange(startIso: string, endIso: string): string {
  return `${formatTime(startIso)}–${formatTime(endIso)}`
}

/** "Mon 9 Nov" for the local day of an instant. */
export function formatBlockDay(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })
}

/** Minutes between two local inputs, or null when either is missing or invalid. */
export function inputMinutes(date: string, start: string, end: string): number | null {
  if (!date || !start || !end) return null
  const from = localDate(date, start).getTime()
  const to = localDate(date, end).getTime()
  if (Number.isNaN(from) || Number.isNaN(to)) return null
  return Math.round((to - from) / 60000)
}

export const END_BEFORE_START = 'The end time must be after the start time.'
export const WINDOW_INCOMPLETE = 'Choose a date, a start time, and an end time.'

/** The dialog's window check: a message to show, or null when the window is valid. */
export function windowError(date: string, start: string, end: string): string | null {
  const minutes = inputMinutes(date, start, end)
  if (minutes === null) return WINDOW_INCOMPLETE
  if (minutes <= 0) return END_BEFORE_START
  return null
}

/** "1h 30m" for a session length. */
export function formatDuration(minutes: number): string {
  return formatMinutes(minutes)
}

/** Ancestors only: "Become a capable engineer › Backend skills › Rust fundamentals". */
export function pathLabel(path: ItemRef[]): string {
  return path.map((ref) => ref.title).join(' › ')
}

export const BLOCK_STATUS_LABELS: Record<TimeBlockStatus, string> = {
  scheduled: 'Planned',
  completed: 'Session done',
  cancelled: 'Cancelled',
  missed: 'Didn’t happen',
}

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  completed: 'Done',
}

// --- Weeks (Calendar) ---------------------------------------------------------------------

/** The Monday (local) of the week that contains `date`. */
export function weekStart(date: string): string {
  const value = localDate(date)
  const offset = (value.getDay() + 6) % 7
  value.setDate(value.getDate() - offset)
  return isoDate(value)
}

export function addDays(date: string, days: number): string {
  const value = localDate(date)
  value.setDate(value.getDate() + days)
  return isoDate(value)
}

/** The seven local dates Monday–Sunday starting at `monday`. */
export function weekDays(monday: string): string[] {
  return Array.from({ length: 7 }, (_, index) => addDays(monday, index))
}

/** UTC bounds [start, end) of the local week starting at `monday`, for `/views/calendar`. */
export function weekRangeUtc(monday: string): { start: string; end: string } {
  return { start: localToUtc(monday, '00:00'), end: localToUtc(addDays(monday, 7), '00:00') }
}

/** "9–15 Nov 2026" (or "30 Nov – 6 Dec 2026") for a week's heading. */
export function weekLabel(monday: string): string {
  const first = localDate(monday)
  const last = localDate(addDays(monday, 6))
  const year = last.getFullYear()
  const lastLabel = last.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
  if (first.getMonth() === last.getMonth()) return `${first.getDate()}–${lastLabel} ${year}`
  const firstLabel = first.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
  return `${firstLabel} – ${lastLabel} ${year}`
}

/**
 * Where a block sits in one local day column, in minutes from midnight, clipped to the day.
 * Null when the block does not touch that day. A block across midnight shows in both days.
 */
export function dayPlacement(
  startIso: string,
  endIso: string,
  day: string,
): { top: number; height: number } | null {
  const dayStart = localDate(day).getTime()
  const dayEnd = localDate(addDays(day, 1)).getTime()
  const start = new Date(startIso).getTime()
  const end = new Date(endIso).getTime()
  if (end <= dayStart || start >= dayEnd) return null
  const top = (Math.max(start, dayStart) - dayStart) / 60000
  const bottom = (Math.min(end, dayEnd) - dayStart) / 60000
  return { top, height: bottom - top }
}

/**
 * Side-by-side lanes for blocks drawn in one day column, so blocks the API marks as
 * overlapping stay readable. Layout only: input is [id, top, height] in placement minutes.
 */
export function assignLanes(
  items: { id: number; top: number; height: number }[],
): Map<number, { lane: number; lanes: number }> {
  const sorted = [...items].sort((a, b) => a.top - b.top || b.height - a.height || a.id - b.id)
  const result = new Map<number, { lane: number; lanes: number }>()
  let group: { id: number; lane: number }[] = []
  let laneEnds: number[] = []
  let groupEnd = Number.NEGATIVE_INFINITY
  const flush = () => {
    for (const item of group) result.set(item.id, { lane: item.lane, lanes: laneEnds.length })
    group = []
    laneEnds = []
  }
  for (const item of sorted) {
    if (item.top >= groupEnd) {
      flush()
      groupEnd = Number.NEGATIVE_INFINITY
    }
    let lane = laneEnds.findIndex((end) => end <= item.top)
    if (lane === -1) {
      lane = laneEnds.length
      laneEnds.push(0)
    }
    laneEnds[lane] = item.top + item.height
    groupEnd = Math.max(groupEnd, item.top + item.height)
    group.push({ id: item.id, lane })
  }
  flush()
  return result
}

// --- Defaults -----------------------------------------------------------------------------

/** A sensible start for a new session: the next half hour from `now`, local. */
export function nextHalfHour(now = new Date()): LocalParts {
  const value = new Date(now)
  value.setSeconds(0, 0)
  const minutes = value.getMinutes()
  value.setMinutes(minutes < 30 ? 30 : 60)
  return { date: isoDate(value), time: `${pad(value.getHours())}:${pad(value.getMinutes())}` }
}

/** `time` plus `minutes`, capped at 23:59 so a default never spills into the next day. */
export function addMinutesToTime(time: string, minutes: number): string {
  const [hours, mins] = time.split(':').map(Number)
  const total = Math.min(23 * 60 + 59, hours * 60 + mins + minutes)
  return `${pad(Math.floor(total / 60))}:${pad(total % 60)}`
}

// --- First-time "Outcome achieved" confirmation ------------------------------------------

export const OUTCOME_LEARNED_KEY = 'atlas.quests.outcomeConfirmed'

/** True once the person has confirmed "Outcome achieved" before (then we stop asking). */
export function outcomeLearned(storage: Pick<Storage, 'getItem'> | null = safeStorage()): boolean {
  return storage?.getItem(OUTCOME_LEARNED_KEY) === '1'
}

export function markOutcomeLearned(storage: Pick<Storage, 'setItem'> | null = safeStorage()): void {
  storage?.setItem(OUTCOME_LEARNED_KEY, '1')
}

function safeStorage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage
  } catch {
    return null
  }
}

/**
 * Whether a session's start has passed. A session that has started is answered with "Didn't
 * happen" (it counts as not kept); one still ahead is called off with "Cancel".
 */
export function hasStarted(block: { start_at: string }, now: Date = new Date()): boolean {
  return new Date(block.start_at).getTime() <= now.getTime()
}
