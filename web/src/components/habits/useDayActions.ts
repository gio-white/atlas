import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import {
  ApiError,
  clearHabitDay,
  createFreeze,
  deleteFreeze,
  type HabitDayResult,
  type HabitFreeze,
  setHabitDay,
} from '@/lib/api'
import { ownDayFreeze, type RowAction } from '@/lib/habits'

/**
 * The writes behind a habit's day, shared by the Day tab, the Week tab, and the habit page:
 * ticking, the row menu's actions, then `reload`. `busy` is the `slug:day` being saved; a failed
 * write leaves its message in `error`.
 */
export function useDayActions(reload: () => Promise<void>) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run(key: string, write: () => Promise<unknown>) {
    setBusy(key)
    setError(null)
    try {
      await write()
      await reload()
    } catch (caught: unknown) {
      setError(caught instanceof ApiError ? caught.message : 'Couldn’t save that. Try again.')
    } finally {
      setBusy(null)
    }
  }

  /** Tick a habit you tick: a Done day's mark is removed, any other day becomes Done. */
  function toggle(slug: string, result: HabitDayResult) {
    void run(`${slug}:${result.day}`, () =>
      result.status === 'done'
        ? clearHabitDay(slug, result.day)
        : setHabitDay(slug, result.day, 'done'),
    )
  }

  function act(slug: string, day: string, action: RowAction, freezes: HabitFreeze[]) {
    const key = `${slug}:${day}`
    switch (action) {
      case 'mark_done':
        return void run(key, () => setHabitDay(slug, day, 'done'))
      case 'mark_not_done':
        return void run(key, () => setHabitDay(slug, day, 'not_done'))
      case 'use_data':
        return void run(key, () => clearHabitDay(slug, day))
      case 'freeze':
        return void run(key, () => createFreeze({ habit: slug, start_on: day, end_on: day }))
      case 'unfreeze': {
        const freeze = ownDayFreeze(freezes, slug, day)
        if (freeze !== undefined) void run(key, () => deleteFreeze(freeze.id))
        return
      }
      case 'open': {
        const on = params.get('on')
        return navigate({
          pathname: `/habit/${slug}`,
          search: on === null ? '' : new URLSearchParams({ on }).toString(),
        })
      }
    }
  }

  return {
    busy,
    error,
    toggle,
    act,
    isBusy: (slug: string, day: string) => busy === `${slug}:${day}`,
  }
}
