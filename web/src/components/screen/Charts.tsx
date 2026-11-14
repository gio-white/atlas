import type {
  ScreenCategoryShare,
  ScreenDayBar,
  ScreenDeviceShare,
  ScreenJudgment,
} from '@/lib/api'
import { shortDateLabel, weekdayLabel } from '@/lib/dates'
import { formatMinutes } from '@/lib/format'
import { cn } from '@/lib/utils'

export const JUDGMENT_LABEL: Record<ScreenJudgment, string> = {
  useful: 'Good',
  waste: 'Bad',
  neutral: 'Neutral',
}

export const JUDGMENT_FILL: Record<ScreenJudgment, string> = {
  useful: 'fill-good',
  waste: 'fill-bad',
  neutral: 'fill-warn',
}

export const JUDGMENT_STROKE: Record<ScreenJudgment, string> = {
  useful: 'stroke-good',
  waste: 'stroke-bad',
  neutral: 'stroke-warn',
}

export const JUDGMENT_BG: Record<ScreenJudgment, string> = {
  useful: 'bg-good',
  waste: 'bg-bad',
  neutral: 'bg-warn',
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const HOURS = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
] as const

export function ScoreRing({
  score,
  band,
}: {
  score: number | null
  band: 'good' | 'ok' | 'poor' | null
}) {
  const pct = score === null ? 0 : Math.min(100, Math.max(0, score))
  const radius = 42
  const circ = 2 * Math.PI * radius
  const offset = circ * (1 - pct / 100)
  const stroke = band === 'good' ? 'stroke-good' : band === 'ok' ? 'stroke-warn' : 'stroke-bad'
  return (
    <div className="relative size-24">
      <svg viewBox="0 0 100 100" className="size-24 -rotate-90" role="img" aria-label="Score">
        <title>Score</title>
        <circle cx="50" cy="50" r={radius} fill="none" className="stroke-raised" strokeWidth="10" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          className={score === null ? 'stroke-raised' : stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <p className="text-lg font-semibold leading-none">{score === null ? '—' : score}</p>
        <p className="mt-1 text-[10px] uppercase tracking-wide text-muted">
          {band === null ? 'score' : band}
        </p>
      </div>
    </div>
  )
}

const BAR_AXIS = 34
const BAR_FOOT = 16
const BAR_TOP = 8

/** Step between y-axis ticks so a chart gets three to five gridlines. */
export function minuteTicks(max: number): number[] {
  const steps = [15, 30, 60, 120, 180, 240, 360, 480, 720]
  const step = steps.find((candidate) => max / candidate <= 4) ?? 720
  const top = Math.max(step, Math.ceil(max / step) * step)
  const ticks: number[] = []
  for (let tick = 0; tick <= top; tick += step) ticks.push(tick)
  return ticks
}

function barLabel(date: string, index: number, count: number): string | null {
  if (count <= 7) return weekdayLabel(date).slice(0, 2)
  return (count - 1 - index) % 5 === 0 ? String(Number(date.slice(8))) : null
}

export function StackedJudgmentBars({
  days,
  breakdown,
}: {
  days: ScreenDayBar[]
  breakdown: boolean
}) {
  const ticks = minuteTicks(Math.max(...days.map((day) => day.total), 1))
  const max = ticks.at(-1) ?? 60
  const width = 560
  const height = 180
  const plot = height - BAR_FOOT - BAR_TOP
  const column = (width - BAR_AXIS) / Math.max(1, days.length)
  const barWidth = Math.min(40, column * 0.7)
  const h = (minutes: number) => (minutes / max) * plot
  const base = BAR_TOP + plot
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-auto w-full"
      role="img"
      aria-label="Daily screen time"
    >
      <title>Daily screen time</title>
      {ticks.map((tick) => (
        <g key={tick}>
          <line
            x1={BAR_AXIS}
            x2={width}
            y1={base - h(tick)}
            y2={base - h(tick)}
            className="stroke-line"
            strokeWidth="1"
          />
          <text
            x="0"
            y={base - h(tick)}
            dominantBaseline="middle"
            className="fill-muted text-[10px] tabular-nums"
          >
            {formatMinutes(tick)}
          </text>
        </g>
      ))}
      {days.map((day, index) => {
        const cx = BAR_AXIS + column * index + column / 2
        const x = cx - barWidth / 2
        const label = barLabel(day.date, index, days.length)
        const stack = breakdown
          ? [
              { key: 'useful', minutes: day.useful, fill: JUDGMENT_FILL.useful },
              { key: 'neutral', minutes: day.neutral, fill: JUDGMENT_FILL.neutral },
              { key: 'waste', minutes: day.waste, fill: JUDGMENT_FILL.waste },
            ]
          : [{ key: 'total', minutes: day.total, fill: 'fill-screen' }]
        let top = base
        return (
          <g key={day.date}>
            <title>
              {shortDateLabel(day.date)} · {formatMinutes(day.total)}
              {breakdown
                ? ` (Good ${formatMinutes(day.useful)}, Neutral ${formatMinutes(day.neutral)}, Bad ${formatMinutes(day.waste)})`
                : ''}
            </title>
            {stack.map((part) => {
              const partHeight = h(part.minutes)
              top -= partHeight
              return partHeight <= 0 ? null : (
                <rect
                  key={part.key}
                  x={x}
                  y={top}
                  width={barWidth}
                  height={partHeight}
                  className={part.fill}
                />
              )
            })}
            {label !== null && (
              <text
                x={cx}
                y={height - 2}
                textAnchor="middle"
                className={cn('text-[10px]', index === days.length - 1 ? 'fill-ink' : 'fill-muted')}
              >
                {label}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export function ComparisonLines({ points }: { points: { current: number; previous: number }[] }) {
  const width = 560
  const height = 140
  const max = Math.max(...points.flatMap((point) => [point.current, point.previous]), 1)
  const toPoints = (values: number[]) =>
    values
      .map((value, index) => {
        const x = values.length === 1 ? 0 : (index / (values.length - 1)) * width
        const y = height - (value / max) * (height - 8) - 4
        return `${x},${y}`
      })
      .join(' ')
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-36 w-full"
      role="img"
      aria-label="This period vs last"
    >
      <title>This period vs last</title>
      <polyline
        fill="none"
        stroke="currentColor"
        className="text-muted"
        strokeWidth="2"
        strokeDasharray="4 4"
        points={toPoints(points.map((point) => point.previous))}
      />
      <polyline
        fill="none"
        stroke="currentColor"
        className="text-screen"
        strokeWidth="2.5"
        points={toPoints(points.map((point) => point.current))}
      />
    </svg>
  )
}

export function ShareDonut({
  slices,
  label,
}: {
  slices: {
    slug: string
    name: string
    minutes: number
    stroke: string
    swatch: string
    detail?: string
  }[]
  label: string
}) {
  const total = slices.reduce((sum, slice) => sum + slice.minutes, 0)
  const radius = 36
  const circ = 2 * Math.PI * radius
  let offset = 0
  return (
    <div className="flex flex-wrap items-center gap-4">
      <svg viewBox="0 0 100 100" className="size-28 -rotate-90" role="img" aria-label={label}>
        <title>{label}</title>
        <circle cx="50" cy="50" r={radius} fill="none" className="stroke-raised" strokeWidth="14" />
        {total > 0 &&
          slices.map((slice) => {
            const length = (slice.minutes / total) * circ
            const circle = (
              <circle
                key={slice.slug}
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                className={slice.stroke}
                strokeWidth="14"
                strokeDasharray={`${length} ${circ - length}`}
                strokeDashoffset={-offset}
              />
            )
            offset += length
            return circle
          })}
      </svg>
      <ul className="flex min-w-0 flex-col gap-1.5 text-xs">
        {slices.length === 0 ? (
          <li className="text-muted">No screen time in this range.</li>
        ) : (
          slices.map((slice) => (
            <li key={slice.slug} className="flex items-start gap-2">
              <span className={cn('mt-1 size-2 shrink-0 rounded-full', slice.swatch)} aria-hidden />
              <span className="flex min-w-0 flex-col">
                <span className="truncate text-ink">{slice.name}</span>
                <span className="whitespace-nowrap tabular-nums text-muted">
                  {formatMinutes(slice.minutes)}
                  {slice.detail !== undefined ? ` · ${slice.detail}` : ''}
                </span>
              </span>
            </li>
          ))
        )}
      </ul>
    </div>
  )
}

export function HourHeatmap({
  hours,
  period,
}: {
  hours: number[][]
  period: 'day' | 'week' | 'month'
}) {
  const max = Math.max(...hours.flat(), 1)
  const labels =
    period === 'day' ? ['Day'] : period === 'week' ? WEEKDAYS : WEEKDAYS.map((day) => `${day} avg`)
  return (
    <div className="overflow-x-auto">
      <div
        className="grid gap-0.5"
        style={{ gridTemplateColumns: `3.5rem repeat(24, minmax(0.5rem, 1fr))` }}
        role="img"
        aria-label="Hour heatmap"
      >
        <span />
        {HOURS.map((hour) => (
          <span key={`h${hour}`} className="text-center text-[9px] text-muted">
            {hour % 3 === 0 ? hour : ''}
          </span>
        ))}
        {hours.map((row, rowIndex) => {
          const label = labels[rowIndex] ?? WEEKDAYS[rowIndex] ?? 'row'
          return (
            <div key={label} className="contents">
              <span className="truncate text-[10px] text-muted">{label}</span>
              {HOURS.map((hour) => {
                const value = row[hour] ?? 0
                return (
                  <span
                    key={`${label}-h${hour}`}
                    className="aspect-square rounded-[2px] bg-screen"
                    style={{ opacity: value <= 0 ? 0.08 : 0.2 + (value / max) * 0.8 }}
                    title={`${label} ${hour}:00 · ${Math.round(value)}m`}
                  />
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function deviceSlices(devices: ScreenDeviceShare[]) {
  const palette = [
    { stroke: 'stroke-screen', swatch: 'bg-screen' },
    { stroke: 'stroke-goal', swatch: 'bg-goal' },
    { stroke: 'stroke-iris', swatch: 'bg-iris' },
    { stroke: 'stroke-ember', swatch: 'bg-ember' },
    { stroke: 'stroke-warn', swatch: 'bg-warn' },
  ]
  return devices.map((device, index) => ({
    slug: device.slug,
    name: device.name,
    minutes: device.minutes,
    ...palette[index % palette.length],
  }))
}

/**
 * Distinct hues for categories. Good / Bad / Neutral colours are left out on purpose, so a
 * category's colour never reads as a judgment.
 */
export const CATEGORY_PALETTE = [
  { stroke: 'stroke-screen', swatch: 'bg-screen' },
  { stroke: 'stroke-ember', swatch: 'bg-ember' },
  { stroke: 'stroke-adventure', swatch: 'bg-adventure' },
  { stroke: 'stroke-library', swatch: 'bg-library' },
  { stroke: 'stroke-iris', swatch: 'bg-iris' },
  { stroke: 'stroke-health', swatch: 'bg-health' },
  { stroke: 'stroke-stage-light', swatch: 'bg-stage-light' },
  { stroke: 'stroke-stage-awake', swatch: 'bg-stage-awake' },
] as const

/**
 * Slices coloured per category. Colours follow the alphabetical order of every known category
 * slug, so a category keeps its colour when the period or the ranking changes.
 */
export function categorySlices(categories: ScreenCategoryShare[], known: string[] = []) {
  const order = [...new Set([...known, ...categories.map((category) => category.slug)])].sort()
  return categories.map((category) => ({
    slug: category.slug,
    name: category.name,
    minutes: category.minutes,
    detail: JUDGMENT_LABEL[category.judgment],
    ...CATEGORY_PALETTE[order.indexOf(category.slug) % CATEGORY_PALETTE.length],
  }))
}
