import { useCallback, useEffect, useState } from 'react'

import {
  ApiError,
  type LibraryTitle,
  type LibraryTopic,
  listLibraryTitles,
  listLibraryTopics,
} from '@/lib/api'

/** Every title and tag, loaded once per page, with a refresh for after edits. */
export function useLibrary() {
  const [titles, setTitles] = useState<LibraryTitle[] | null>(null)
  const [topics, setTopics] = useState<LibraryTopic[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextTitles, nextTopics] = await Promise.all([
      listLibraryTitles(),
      listLibraryTopics().catch(() => []),
    ])
    setTitles(nextTitles)
    setTopics(nextTopics)
  }, [])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Couldn’t load the library.')
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  return { titles, topics, error, refresh }
}
