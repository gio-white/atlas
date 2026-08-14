import type { ScreenDayBar, ScreenDeviceShare, ScreenJudgment } from '@/lib/api'
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

export function StackedJudgmentBars({
  days,
  breakdown,
}: {
  days: ScreenDayBar[]
  breakdown: boolean
}) {
  const max = Math.max(...days.map((day) => day.total), 1)
  const width = Math.max(days.length * 28, 240)
  const height = 140
  const gap = 4
  const barWidth = days.length === 0 ? 0 : (width - gap * (days.length - 1)) / days.length
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="h-36 w-full"
      role="img"
      aria-label="Daily screen time"
    >
      <title>Daily screen time</title>
      {days.map((day, index) => {
        const x = index * (barWidth + gap)
        if (!breakdown) {
          const h = (day.total / max) * (height - 4)
          return (
            <rect
              key={day.date}
              x={x}
              y={height - h}
              width={barWidth}
              height={h}
              className="fill-screen"
              rx="3"
            />
          )
        }
        const usefulH = (day.useful / max) * (height - 4)
        const wasteH = (day.waste / max) * (height - 4)
        const neutralH = (day.neutral / max) * (height - 4)
        const wasteY = height - usefulH - wasteH
        const neutralY = wasteY - neutralH
        return (
          <g key={day.date}>
            <rect
              x={x}
              y={height - usefulH}
              width={barWidth}
              height={usefulH}
              className="fill-good"
              rx="2"
            />
            <rect x={x} y={wasteY} width={barWidth} height={wasteH} className="fill-bad" />
            <rect x={x} y={neutralY} width={barWidth} height={neutralH} className="fill-warn" />
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
  slices: { slug: string; name: string; minutes: number; stroke: string; swatch: string }[]
  label: string
}) {
  const total = slices.reduce((sum, slice) => sum + slice.minutes, 0)
  const radius = 36
  const circ = 2 * Math.PI * radius
  let offset = 0
  return (
    <div className="flex items-center gap-4">
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
      <ul className="flex flex-col gap-1 text-xs">
        {slices.length === 0 ? (
          <li className="text-muted">No minutes in range.</li>
        ) : (
          slices.map((slice) => (
            <li key={slice.slug} className="flex items-center gap-2">
              <span className={cn('size-2 rounded-full', slice.swatch)} />
              {slice.name}
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
    { stroke: 'stroke-update', swatch: 'bg-update' },
    { stroke: 'stroke-slip', swatch: 'bg-slip' },
    { stroke: 'stroke-warn', swatch: 'bg-warn' },
  ]
  return devices.map((device, index) => ({
    slug: device.slug,
    name: device.name,
    minutes: device.minutes,
    ...palette[index % palette.length],
  }))
}
