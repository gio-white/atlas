import { Check, Flame, Plus, SkipForward, Undo2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  ApiError,
  addHabitBreak,
  checkInHabit,
  deleteHabitBreak,
  getHabitDetail,
  type HabitStatus,
  undoHabitCheckIn,
} from '@/lib/api'
import {
  daysLeftLabel,
  formatAmount,
  goalLabel,
  isOverLimit,
  progressOf,
  quickAmounts,
  streakLabel,
  targetFor,
} from '@/lib/habits'
import { cn } from '@/lib/utils'

type Action = () => Promise<unknown>

/**
 * One habit's check-in surface for a day. Daily habits render as a card; weekly and
 * monthly habits as a row with a progress bar (`layout="row"`).
 */
export function HabitCard({
  status,
  asOf,
  search,
  onChanged,
  layout = 'card',
}: {
  status: HabitStatus
  asOf: string
  search: string
  onChanged: () => Promise<void>
  layout?: 'card' | 'row'
}) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [custom, setCustom] = useState<string | null>(null)
  const [slipNote, setSlipNote] = useState<string | null>(null)

  async function run(action: Action) {
    setPending(true)
    setError(null)
    try {
      await action()
      await onChanged()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not save')
    } finally {
      setPending(false)
    }
  }

  const add = (amount?: number, note?: string) =>
    run(() => checkInHabit(status.slug, { amount, on: asOf, note: note || null }, asOf))
  const undo = () => run(() => undoHabitCheckIn(status.slug, asOf, asOf))
  const skip = () => run(() => addHabitBreak(status.slug, { start_on: asOf }))
  const unskip = () =>
    run(async () => {
      const detail = await getHabitDetail(status.slug, asOf)
      const today = detail.breaks.find((row) => row.start_on === asOf && row.end_on === asOf)
      if (today === undefined) throw new ApiError(400, 'This day is part of a longer pause.')
      await deleteHabitBreak(status.slug, today.id)
    })

  const loggedToday = (status.today_value ?? 0) > 0
  const progress = progressOf(status)
  const over = isOverLimit(status)
  const link = (
    <Link
      to={{ pathname: `/habit/${status.slug}`, search }}
      className="truncate font-medium text-ink hover:underline"
    >
      {status.name}
    </Link>
  )
  const meta = (
    <p className="truncate text-xs text-muted">
      {goalLabel(status)} · <Flame className="inline size-3 text-warn" aria-hidden />{' '}
      {streakLabel(status)}
    </p>
  )

  if (status.skipped_today && status.period === 'day') {
    return (
      <article className="flex items-center gap-3 rounded-2xl border border-dashed border-line bg-surface/60 p-4 opacity-80">
        <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-warn/10 text-warn">
          <SkipForward className="size-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          {link}
          <p className="text-xs text-muted">Skipped today · streak kept</p>
        </div>
        <Button type="button" variant="ghost" size="sm" disabled={pending} onClick={unskip}>
          Undo skip
        </Button>
        {error ? (
          <p className="sr-only" role="alert">
            {error}
          </p>
        ) : null}
      </article>
    )
  }

  if (layout === 'row') {
    const target = targetFor(status)
    return (
      <article className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            {link}
            {meta}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {loggedToday ? (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Undo last check-in for ${status.name}`}
                disabled={pending}
                onClick={undo}
              >
                <Undo2 className="size-4" aria-hidden />
              </Button>
            ) : null}
            <QuickAdds status={status} pending={pending} onAdd={add} todayDone={loggedToday} />
          </div>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-raised">
          <div
            className={cn(
              'h-full rounded-full motion-safe:transition-[width] motion-safe:duration-300',
              status.satisfied ? 'bg-good' : 'bg-update',
            )}
            style={{ width: `${Math.round((progress ?? 0) * 100)}%` }}
          />
        </div>
        <p className="flex justify-between text-xs text-muted">
          <span>
            {formatAmount(status.current_value, status.kind, status.unit)} of{' '}
            {formatAmount(target, status.kind, status.unit)}
            {target !== status.target_value ? ' (adjusted for your break)' : ''}
          </span>
          <span>{status.satisfied ? 'Done' : daysLeftLabel(status)}</span>
        </p>
        {error ? (
          <p className="text-xs text-bad" role="alert">
            {error}
          </p>
        ) : null}
      </article>
    )
  }

  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-2xl border bg-surface p-4 shadow-[var(--shadow-card)] motion-safe:transition-colors',
        over
          ? 'border-bad/40 bg-bad/5'
          : status.satisfied && status.kind !== 'quit' && status.comparator !== 'at_most'
            ? 'border-good/40 bg-good/5'
            : 'border-line',
      )}
    >
      <div className="flex items-center gap-3">
        {status.kind === 'check' ? (
          <button
            type="button"
            disabled={pending}
            aria-pressed={status.satisfied}
            aria-label={`${status.name}: ${status.satisfied ? 'done, tap to undo' : 'mark done'}`}
            onClick={() => (status.satisfied ? undo() : add())}
            className={cn(
              'flex size-12 shrink-0 cursor-pointer items-center justify-center rounded-full border-2 motion-safe:transition-all motion-safe:active:scale-90',
              status.satisfied
                ? 'border-good bg-good text-white'
                : 'border-line text-muted hover:border-good hover:text-good',
            )}
          >
            <Check className="size-6" aria-hidden />
          </button>
        ) : status.kind === 'quit' ? (
          <div className="flex size-12 shrink-0 flex-col items-center justify-center rounded-full bg-good/10 text-good">
            <span className="text-lg leading-none font-semibold">{status.current_streak}</span>
            <span className="text-[10px] leading-none">clean</span>
          </div>
        ) : (
          <ProgressRing
            value={progress ?? 0}
            done={status.satisfied && status.comparator !== 'at_most'}
            over={over}
          />
        )}
        <div className="min-w-0 flex-1">
          {link}
          {status.kind === 'count' || status.kind === 'duration' ? (
            <p className="text-sm text-ink">
              {formatAmount(status.today_value, status.kind, null)}
              <span className="text-muted">
                {' '}
                / {formatAmount(targetFor(status), status.kind, status.unit)}
              </span>
            </p>
          ) : null}
          {meta}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={`Skip ${status.name} today`}
          title="Skip today (keeps your streak)"
          disabled={pending}
          onClick={skip}
        >
          <SkipForward className="size-4" aria-hidden />
        </Button>
      </div>

      {status.kind === 'count' || status.kind === 'duration' ? (
        <div className="flex flex-wrap items-center gap-2">
          {quickAmounts(status).map((amount) => (
            <Button
              key={amount}
              type="button"
              variant="secondary"
              size="sm"
              disabled={pending}
              onClick={() => add(amount)}
            >
              +{status.kind === 'duration' ? `${amount}m` : amount}
            </Button>
          ))}
          {custom === null ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={pending}
              onClick={() => setCustom('')}
            >
              <Plus className="size-3.5" aria-hidden />
              Other
            </Button>
          ) : (
            <form
              className="flex items-center gap-1"
              onSubmit={(event: FormEvent) => {
                event.preventDefault()
                const amount = Number(custom)
                if (Number.isFinite(amount) && amount > 0) {
                  setCustom(null)
                  void add(amount)
                }
              }}
            >
              <Input
                aria-label={`Amount for ${status.name}`}
                type="number"
                min="0"
                step="any"
                autoFocus
                className="h-8 w-20"
                value={custom}
                onChange={(event) => setCustom(event.target.value)}
              />
              <Button type="submit" size="sm" disabled={pending}>
                Add
              </Button>
            </form>
          )}
          {loggedToday ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="ml-auto"
              disabled={pending}
              onClick={undo}
            >
              <Undo2 className="size-3.5" aria-hidden />
              Undo
            </Button>
          ) : null}
        </div>
      ) : null}

      {status.kind === 'quit' ? (
        slipNote === null ? (
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={pending}
              onClick={() => setSlipNote('')}
            >
              Log a slip
            </Button>
            {loggedToday ? (
              <Button type="button" variant="ghost" size="sm" disabled={pending} onClick={undo}>
                <Undo2 className="size-3.5" aria-hidden />
                Undo slip
              </Button>
            ) : null}
          </div>
        ) : (
          <form
            className="flex items-center gap-2"
            onSubmit={(event: FormEvent) => {
              event.preventDefault()
              const note = slipNote
              setSlipNote(null)
              void add(undefined, note)
            }}
          >
            <Input
              aria-label="What happened (optional)"
              placeholder="What happened? (optional)"
              autoFocus
              className="h-8"
              value={slipNote}
              onChange={(event) => setSlipNote(event.target.value)}
            />
            <Button type="submit" variant="destructive" size="sm" disabled={pending}>
              Log slip
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={() => setSlipNote(null)}>
              Cancel
            </Button>
          </form>
        )
      ) : null}

      {error ? (
        <p className="text-xs text-bad" role="alert">
          {error}
        </p>
      ) : null}
    </article>
  )
}

function QuickAdds({
  status,
  pending,
  todayDone,
  onAdd,
}: {
  status: HabitStatus
  pending: boolean
  todayDone: boolean
  onAdd: (amount?: number) => Promise<void>
}) {
  if (status.kind === 'check') {
    return (
      <Button
        type="button"
        variant={todayDone || status.satisfied ? 'secondary' : 'default'}
        size="sm"
        disabled={pending || todayDone}
        onClick={() => onAdd()}
      >
        <Check className="size-3.5" aria-hidden />
        {todayDone ? 'Done today' : 'Done today?'}
      </Button>
    )
  }
  return (
    <>
      {quickAmounts(status).map((amount) => (
        <Button
          key={amount}
          type="button"
          variant="secondary"
          size="sm"
          disabled={pending}
          onClick={() => onAdd(amount)}
        >
          +{status.kind === 'duration' ? `${amount}m` : amount}
        </Button>
      ))}
    </>
  )
}

export function ProgressRing({
  value,
  done,
  over = false,
  size = 48,
}: {
  value: number
  done: boolean
  over?: boolean
  size?: number
}) {
  const radius = 20
  const circumference = 2 * Math.PI * radius
  return (
    <svg
      viewBox="0 0 48 48"
      width={size}
      height={size}
      className="shrink-0 -rotate-90"
      role="img"
      aria-label={`${Math.round(value * 100)}% done`}
    >
      <circle cx="24" cy="24" r={radius} fill="none" strokeWidth="5" className="stroke-raised" />
      <circle
        cx="24"
        cy="24"
        r={radius}
        fill="none"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - value)}
        className={cn(
          'motion-safe:transition-[stroke-dashoffset] motion-safe:duration-300',
          over ? 'stroke-bad' : done ? 'stroke-good' : 'stroke-update',
        )}
      />
    </svg>
  )
}
