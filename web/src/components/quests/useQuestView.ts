import { useCallback, useEffect, useRef, useState } from 'react'

import { ApiError } from '@/lib/api'

export function errorMessage(caught: unknown, fallback: string): string {
  if (caught instanceof ApiError && caught.status === 0) return caught.message
  return fallback
}

/**
 * Load a quest read model and reload it after any change. `reload` keeps the current data on
 * screen while it refetches, so edits do not flash the loading skeleton.
 */
export function useQuestView<T>(load: () => Promise<T>, fallbackError: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const loadRef = useRef(load)
  loadRef.current = load
  const generation = useRef(0)

  const reload = useCallback(async () => {
    const mine = ++generation.current
    try {
      const next = await loadRef.current()
      if (mine === generation.current) {
        setData(next)
        setError(null)
      }
    } catch (caught) {
      if (mine === generation.current) {
        setError(
          caught instanceof ApiError && caught.status === 404
            ? 'This item no longer exists.'
            : errorMessage(caught, fallbackError),
        )
      }
    }
  }, [fallbackError])

  return { data, error, reload, setData }
}

/** Run `reload` once on mount and again whenever `key` changes (a route id). */
export function useLoadOnKey(reload: () => Promise<void>, key: unknown) {
  useEffect(() => {
    void key
    void reload()
  }, [reload, key])
}
