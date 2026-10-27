import { useCallback, useEffect, useState } from 'react'

import {
  ApiError,
  type EntertainmentTitle,
  type EntertainmentTopic,
  listEntertainmentTitles,
  listEntertainmentTopics,
} from '@/lib/api'

/** Every title and tag, loaded once per page, with a refresh for after edits. */
export function useLibrary() {
  const [titles, setTitles] = useState<EntertainmentTitle[] | null>(null)
  const [topics, setTopics] = useState<EntertainmentTopic[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextTitles, nextTopics] = await Promise.all([
      listEntertainmentTitles(),
      listEntertainmentTopics().catch(() => []),
    ])
    setTitles(nextTitles)
    setTopics(nextTopics)
  }, [])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load entertainment')
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  return { titles, topics, error, refresh }
}
