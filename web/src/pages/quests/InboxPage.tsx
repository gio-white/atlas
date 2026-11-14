import { CornerDownLeft } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { InboxItem, type InboxOutcome } from '@/components/quests/InboxItem'
import { TaskDrawerProvider } from '@/components/quests/TaskDrawer'
import { errorMessage, useQuestView } from '@/components/quests/useQuestView'
import { Input } from '@/components/ui/input'
import { createQuestTask, getInbox } from '@/lib/api'
import { INBOX_CHANGED_EVENT, itemHref, KIND_LABELS, notifyInboxChanged } from '@/lib/quests'

type Notice = { text: string; href?: string; link?: string }

function noticeFor(outcome: InboxOutcome): Notice | null {
  if (outcome.kind === 'organized') return { text: `Sorted into ${outcome.where}.` }
  if (outcome.kind === 'standalone') {
    return { text: 'Now a standalone task.', href: '/quests/side-quests', link: 'See side quests' }
  }
  if (outcome.kind === 'promoted') {
    const { result } = outcome
    const href = itemHref(result) ?? undefined
    return {
      text: `Turned into a ${KIND_LABELS[result.kind].toLowerCase()}: ${result.title}.`,
      href,
      link: href === undefined ? undefined : 'Open it',
    }
  }
  if (outcome.kind === 'archived') return { text: 'Archived.' }
  return null
}

export function InboxPage() {
  const { data, error, reload } = useQuestView(getInbox, "Couldn't load your Inbox.")
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)
  const formRef = useRef<HTMLFormElement>(null)
  const refresh = useCallback(() => void reload(), [reload])

  useEffect(() => {
    void reload()
    // A task added elsewhere (the header's Add → Task) shows up without leaving the page.
    const onChange = () => void reload()
    window.addEventListener(INBOX_CHANGED_EVENT, onChange)
    return () => window.removeEventListener(INBOX_CHANGED_EVENT, onChange)
  }, [reload])

  const focusCapture = useCallback(() => formRef.current?.querySelector('input')?.focus(), [])

  async function capture(event: FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (trimmed === '') return
    setBusy(true)
    setCaptureError(null)
    try {
      await createQuestTask({ title: trimmed })
      setTitle('')
      setNotice(null)
      notifyInboxChanged()
      await reload()
    } catch (caught) {
      setCaptureError(errorMessage(caught, "Couldn't add it. Try again."))
    } finally {
      setBusy(false)
      focusCapture()
    }
  }

  if (error !== null && data === null) {
    return <PageUnavailable tab title="Inbox" message={error} />
  }

  return (
    <TaskDrawerProvider onChanged={refresh}>
      <div className="flex flex-col gap-6">
        <PageHeader
          tab
          title="Inbox"
          description="Capture anything now, sort it later. Only a title is needed."
        />
        <form ref={formRef} onSubmit={capture} className="flex flex-col gap-1">
          <div className="relative">
            <Input
              autoFocus
              aria-label="Capture a task"
              placeholder="What's on your mind?"
              className="h-12 rounded-xl pr-24 text-base"
              value={title}
              readOnly={busy}
              onChange={(event) => setTitle(event.target.value)}
            />
            <span className="pointer-events-none absolute top-1/2 right-3 inline-flex -translate-y-1/2 items-center gap-1 text-xs text-muted">
              <CornerDownLeft className="size-3" aria-hidden />
              Enter to add
            </span>
          </div>
          {captureError !== null && (
            <p role="alert" className="text-sm text-bad">
              {captureError}
            </p>
          )}
        </form>

        <p role="status" aria-live="polite" className="min-h-5 text-sm text-muted">
          {notice !== null && (
            <>
              {notice.text}
              {notice.href !== undefined && (
                <>
                  {' '}
                  <Link to={notice.href} className="text-accent hover:underline">
                    {notice.link}
                  </Link>
                </>
              )}
            </>
          )}
        </p>

        {data === null ? (
          <PageLoading />
        ) : data.tasks.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line bg-raised/50 px-4 py-8 text-center">
            <p className="font-medium text-ink">Inbox zero</p>
            <p className="mt-1 text-sm text-muted">
              Everything is sorted. New ideas you capture above land here first.
            </p>
          </div>
        ) : (
          <section aria-labelledby="inbox-items" className="flex flex-col gap-2">
            <h2 id="inbox-items" className="text-xs font-medium text-muted">
              {data.count === 1 ? '1 item to sort' : `${data.count} items to sort`}
            </h2>
            <ul className="flex flex-col gap-2">
              {data.tasks.map((task) => (
                <InboxItem
                  key={task.id}
                  task={task}
                  onDone={(outcome) => {
                    const next = noticeFor(outcome)
                    if (next !== null) setNotice(next)
                    void reload()
                    if (outcome.kind !== 'edited') focusCapture()
                  }}
                />
              ))}
            </ul>
          </section>
        )}
      </div>
    </TaskDrawerProvider>
  )
}
