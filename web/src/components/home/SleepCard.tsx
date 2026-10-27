import { Moon, Plus, X } from 'lucide-react'
import { type FormEvent, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  logSleepSession,
  type SleepNight,
  type SleepStage,
  type SleepView,
} from '@/lib/api'
import { shiftPeriodDate, weekdayLabel } from '@/lib/dates'
import { formatMinutes } from '@/lib/format'
import {
  formatClock,
  SLEEP_STAGE_META,
  SLEEP_STAGES,
  type StageDraft,
  stageShares,
  stagesFromDrafts,
  weekAxis,
} from '@/lib/sleep'
import { cn } from '@/lib/utils'

export function SleepCard({
  view,
  asOf,
  onLogged,
}: {
  view: SleepView | null
  asOf: string
  onLogged: () => Promise<void>
}) {
  const [logOpen, setLogOpen] = useState(false)
  const night = view?.night ?? null
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Moon className="size-4 text-sleep" aria-hidden />
            Sleep
          </CardTitle>
          <CardDescription>Last night and the past 7 nights</CardDescription>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={() => setLogOpen(true)}>
          <Plus className="size-4" aria-hidden />
          Log night
        </Button>
      </CardHeader>
      {view === null ? (
        <p className="text-sm text-muted">Sleep data is unavailable right now.</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
          <LastNight night={night} />
          <WeekNights view={view} />
        </div>
      )}
      <LogSleepDialog
        open={logOpen}
        onOpenChange={setLogOpen}
        asOf={asOf}
        onLogged={async () => {
          setLogOpen(false)
          await onLogged()
        }}
      />
    </Card>
  )
}

function LastNight({ night }: { night: SleepNight | null }) {
  if (night === null) {
    return (
      <section aria-label="Last night">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Last night</p>
        <p className="mt-2 text-sm text-muted">No night logged that ends today.</p>
      </section>
    )
  }
  const shares = stageShares(night.stages)
  return (
    <section aria-label="Last night" className="flex flex-col gap-3">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Last night</p>
        <p className="text-3xl font-semibold tracking-tight">
          {formatMinutes(night.asleep_minutes)}
        </p>
        <p className="text-sm text-muted">
          {formatClock(night.bed_offset)} → {formatClock(night.wake_offset)} · in bed{' '}
          {formatMinutes(night.in_bed_minutes)}
        </p>
      </div>
      {night.segments.length === 0 ? (
        <p className="text-xs text-muted">No sleep stages recorded for this night.</p>
      ) : (
        <>
          <Hypnogram night={night} />
          <ul className="flex flex-col gap-1 text-xs">
            {shares.map((item) => (
              <li key={item.stage} className="flex items-center gap-2">
                <span
                  className={cn('size-2.5 rounded-sm', SLEEP_STAGE_META[item.stage].bg)}
                  aria-hidden
                />
                <span className="text-ink">{SLEEP_STAGE_META[item.stage].label}</span>
                <span className="ml-auto tabular-nums text-muted">
                  {formatMinutes(item.minutes)} · {Math.round(item.share * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

const HYPNO_STAGES = ['awake', 'rem', 'light', 'deep'] as const
const HYPNO_WIDTH = 300
const HYPNO_LABEL = 40
const HYPNO_LANE = 14
const HYPNO_GAP = 4

function Hypnogram({ night }: { night: SleepNight }) {
  const span = Math.max(1, night.wake_offset - night.bed_offset)
  const plot = HYPNO_WIDTH - HYPNO_LABEL
  const height = HYPNO_STAGES.length * (HYPNO_LANE + HYPNO_GAP) + 12
  const x = (offset: number) => HYPNO_LABEL + ((offset - night.bed_offset) / span) * plot
  return (
    <svg
      viewBox={`0 0 ${HYPNO_WIDTH} ${height}`}
      className="h-auto w-full"
      role="img"
      aria-label="Sleep stages through the night"
    >
      <title>Sleep stages through the night</title>
      {HYPNO_STAGES.map((stage, lane) => {
        const y = lane * (HYPNO_LANE + HYPNO_GAP)
        return (
          <g key={stage}>
            <rect
              x={HYPNO_LABEL}
              y={y}
              width={plot}
              height={HYPNO_LANE}
              rx="3"
              className="fill-raised"
            />
            <text x="0" y={y + HYPNO_LANE - 3} className="fill-muted text-[10px]">
              {SLEEP_STAGE_META[stage].label}
            </text>
          </g>
        )
      })}
      {night.segments.map((segment) => {
        const lane = HYPNO_STAGES.indexOf(segment.stage)
        const start = x(segment.start_offset)
        const width = Math.max(1, x(segment.end_offset) - start)
        return (
          <rect
            key={`${segment.stage}-${segment.start_offset}`}
            x={start}
            y={lane * (HYPNO_LANE + HYPNO_GAP)}
            width={width}
            height={HYPNO_LANE}
            rx="2"
            className={SLEEP_STAGE_META[segment.stage].fill}
          >
            <title>
              {SLEEP_STAGE_META[segment.stage].label} {formatClock(segment.start_offset)}–
              {formatClock(segment.end_offset)} ·{' '}
              {formatMinutes(segment.end_offset - segment.start_offset)}
            </title>
          </rect>
        )
      })}
      <text x={HYPNO_LABEL} y={height - 1} className="fill-muted text-[10px]">
        {formatClock(night.bed_offset)}
      </text>
      <text x={HYPNO_WIDTH} y={height - 1} textAnchor="end" className="fill-muted text-[10px]">
        {formatClock(night.wake_offset)}
      </text>
    </svg>
  )
}

const WEEK_WIDTH = 300
const WEEK_HEIGHT = 170
const WEEK_AXIS = 34
const WEEK_FOOT = 16

function WeekNights({ view }: { view: SleepView }) {
  const axis = weekAxis(view)
  const plotHeight = WEEK_HEIGHT - WEEK_FOOT
  const column = (WEEK_WIDTH - WEEK_AXIS) / view.days.length
  const barWidth = Math.min(18, column * 0.55)
  const y = (offset: number) => ((offset - axis.start) / (axis.end - axis.start)) * plotHeight
  return (
    <section aria-label="Past 7 nights" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Past 7 nights</p>
        <p className="text-xs text-muted">{view.nights_logged}/7 logged</p>
      </div>
      <dl className="grid grid-cols-3 gap-2 text-xs">
        <WeekStat label="Avg sleep" value={formatMinutes(view.average_asleep)} />
        <WeekStat label="Avg bedtime" value={formatClock(view.average_bed_offset)} />
        <WeekStat label="Avg wake" value={formatClock(view.average_wake_offset)} />
      </dl>
      <svg
        viewBox={`0 0 ${WEEK_WIDTH} ${WEEK_HEIGHT}`}
        className="h-auto w-full"
        role="img"
        aria-label="Bedtime and wake time for the past 7 nights"
      >
        <title>Bedtime and wake time for the past 7 nights</title>
        {axis.ticks.map((tick) => (
          <g key={tick}>
            <line
              x1={WEEK_AXIS}
              x2={WEEK_WIDTH}
              y1={y(tick)}
              y2={y(tick)}
              className="stroke-line"
              strokeWidth="1"
            />
            <text x="0" y={y(tick) + 3} className="fill-muted text-[10px] tabular-nums">
              {formatClock(tick)}
            </text>
          </g>
        ))}
        {view.days.map((day, index) => {
          const cx = WEEK_AXIS + column * index + column / 2
          const night = day.night
          return (
            <g key={day.date}>
              <text
                x={cx}
                y={WEEK_HEIGHT - 2}
                textAnchor="middle"
                className={cn('text-[10px]', index === 6 ? 'fill-ink' : 'fill-muted')}
              >
                {weekdayLabel(day.date).slice(0, 2)}
              </text>
              {night !== null && (
                <g>
                  <title>
                    {weekdayLabel(day.date)} {day.date.slice(8)} · {formatClock(night.bed_offset)} →{' '}
                    {formatClock(night.wake_offset)} · {formatMinutes(night.asleep_minutes)} asleep
                  </title>
                  {night.segments.length === 0 ? (
                    <rect
                      x={cx - barWidth / 2}
                      y={y(night.bed_offset)}
                      width={barWidth}
                      height={Math.max(2, y(night.wake_offset) - y(night.bed_offset))}
                      rx="4"
                      className="fill-sleep"
                    />
                  ) : (
                    <>
                      <clipPath id={`night-${day.date}`}>
                        <rect
                          x={cx - barWidth / 2}
                          y={y(night.bed_offset)}
                          width={barWidth}
                          height={Math.max(2, y(night.wake_offset) - y(night.bed_offset))}
                          rx="4"
                        />
                      </clipPath>
                      <g clipPath={`url(#night-${day.date})`}>
                        {night.segments.map((segment) => (
                          <rect
                            key={`${segment.stage}-${segment.start_offset}`}
                            x={cx - barWidth / 2}
                            y={y(segment.start_offset)}
                            width={barWidth}
                            height={Math.max(0.5, y(segment.end_offset) - y(segment.start_offset))}
                            className={SLEEP_STAGE_META[segment.stage].fill}
                          />
                        ))}
                      </g>
                    </>
                  )}
                  <rect
                    x={cx - column / 2}
                    y={0}
                    width={column}
                    height={plotHeight}
                    fill="transparent"
                  />
                </g>
              )}
            </g>
          )
        })}
      </svg>
      <ul className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted" aria-label="Stages">
        {SLEEP_STAGES.map((stage) => (
          <li key={stage} className="flex items-center gap-1.5">
            <span className={cn('size-2 rounded-sm', SLEEP_STAGE_META[stage].bg)} aria-hidden />
            {SLEEP_STAGE_META[stage].label}
          </li>
        ))}
      </ul>
    </section>
  )
}

function WeekStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-raised px-2 py-1.5">
      <dt className="text-muted">{label}</dt>
      <dd className="text-sm font-semibold tabular-nums text-ink">{value}</dd>
    </div>
  )
}

function LogSleepDialog({
  open,
  onOpenChange,
  asOf,
  onLogged,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  asOf: string
  onLogged: () => Promise<void>
}) {
  const [bed, setBed] = useState(`${shiftPeriodDate(asOf, 'day', -1)}T23:00`)
  const [wake, setWake] = useState(`${asOf}T07:00`)
  const [stages, setStages] = useState<(StageDraft & { id: number })[]>([])
  const nextStageId = useRef(0)
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  function updateStage(index: number, patch: Partial<StageDraft>) {
    setStages((rows) => rows.map((row, at) => (at === index ? { ...row, ...patch } : row)))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      await logSleepSession({
        started_at: new Date(bed).toISOString(),
        ended_at: new Date(wake).toISOString(),
        stages: stagesFromDrafts(stages),
        note: note.trim() === '' ? null : note.trim(),
      })
      setStages([])
      setNote('')
      await onLogged()
    } catch (caught) {
      setError(
        caught instanceof ApiError || caught instanceof Error
          ? caught.message
          : 'Could not log sleep',
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Log a night</DialogTitle>
          <DialogDescription>
            When you went to bed and woke up. Stages are optional; add them if a tracker gave you
            deep, light, REM, and awake times.
          </DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-3" onSubmit={(event) => void onSubmit(event)}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="sleep-bed">Went to bed</Label>
            <Input
              id="sleep-bed"
              type="datetime-local"
              value={bed}
              onChange={(event) => setBed(event.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="sleep-wake">Woke up</Label>
            <Input
              id="sleep-wake"
              type="datetime-local"
              value={wake}
              onChange={(event) => setWake(event.target.value)}
              required
            />
          </div>
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-sm font-medium text-ink">Stages</legend>
            {stages.map((row, index) => (
              <div
                key={row.id}
                className="grid grid-cols-[6rem_minmax(0,1fr)_minmax(0,1fr)_auto] items-end gap-2"
              >
                <Select
                  aria-label={`Stage ${index + 1}`}
                  value={row.stage}
                  onChange={(event) =>
                    updateStage(index, { stage: event.target.value as SleepStage })
                  }
                >
                  {SLEEP_STAGES.map((stage) => (
                    <option key={stage} value={stage}>
                      {SLEEP_STAGE_META[stage].label}
                    </option>
                  ))}
                </Select>
                <Input
                  type="datetime-local"
                  aria-label={`Stage ${index + 1} start`}
                  value={row.started}
                  onChange={(event) => updateStage(index, { started: event.target.value })}
                />
                <Input
                  type="datetime-local"
                  aria-label={`Stage ${index + 1} end`}
                  value={row.ended}
                  onChange={(event) => updateStage(index, { ended: event.target.value })}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Remove stage ${index + 1}`}
                  onClick={() => setStages((rows) => rows.filter((_, at) => at !== index))}
                >
                  <X className="size-4" aria-hidden />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="self-start"
              onClick={() =>
                setStages((rows) => [
                  ...rows,
                  {
                    id: nextStageId.current++,
                    stage: 'light',
                    started: rows.at(-1)?.ended ?? bed,
                    ended: rows.at(-1)?.ended ?? bed,
                  },
                ])
              }
            >
              <Plus className="size-4" aria-hidden />
              Add stage
            </Button>
          </fieldset>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="sleep-note">Note</Label>
            <Input id="sleep-note" value={note} onChange={(event) => setNote(event.target.value)} />
          </div>
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" disabled={pending}>
            Save night
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
