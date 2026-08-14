import { cn } from '@/lib/utils'

function points(values: number[], width: number, height: number): string {
  if (values.length === 0) return ''
  const max = Math.max(...values, 1)
  return values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width
      const y = height - (value / max) * height
      return `${x},${y}`
    })
    .join(' ')
}

const HOUR_KEYS = ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22']

export function Sparkline({ values, className }: { values: number[]; className?: string }) {
  const width = 120
  const height = 36
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={cn('h-9 w-28 overflow-visible', className)}
      role="img"
      aria-label="Trend"
    >
      <title>Trend</title>
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        points={points(values, width, height)}
      />
    </svg>
  )
}

export function HourBars({ values, className }: { values: number[]; className?: string }) {
  const max = Math.max(...values, 1)
  return (
    <div className={cn('flex h-16 items-end gap-1', className)} aria-hidden>
      {values.map((value, index) => (
        <div
          key={HOUR_KEYS[index] ?? `h${value}`}
          className="min-w-0 flex-1 rounded-sm bg-current"
          style={{ height: `${Math.max(8, (value / max) * 100)}%` }}
        />
      ))}
    </div>
  )
}

export function AreaChart({
  seriesA,
  seriesB,
  labels,
}: {
  seriesA: number[]
  seriesB: number[]
  labels: string[]
}) {
  const width = 560
  const height = 140
  const max = Math.max(...seriesA, ...seriesB, 1)
  const toPoints = (values: number[]) =>
    values
      .map((value, index) => {
        const x = values.length === 1 ? 0 : (index / (values.length - 1)) * width
        const y = height - (value / max) * (height - 8) - 4
        return `${x},${y}`
      })
      .join(' ')
  const area = (values: number[]) => {
    const line = toPoints(values)
    return `0,${height} ${line} ${width},${height}`
  }
  return (
    <div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-36 w-full"
        role="img"
        aria-label="Weekly trend"
      >
        <title>Weekly trend</title>
        <polygon fill="currentColor" className="text-update/25" points={area(seriesA)} />
        <polyline
          fill="none"
          stroke="currentColor"
          className="text-update"
          strokeWidth="2.5"
          points={toPoints(seriesA)}
        />
        <polygon fill="currentColor" className="text-screen/20" points={area(seriesB)} />
        <polyline
          fill="none"
          stroke="currentColor"
          className="text-screen"
          strokeWidth="2.5"
          points={toPoints(seriesB)}
        />
      </svg>
      <div className="mt-1 flex justify-between text-[11px] text-muted">
        {labels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
    </div>
  )
}

export function ProgressRing({ value, label }: { value: number | null; label: string }) {
  const pct = value === null ? 0 : Math.round(Math.min(1, Math.max(0, value)) * 100)
  const radius = 42
  const circ = 2 * Math.PI * radius
  const offset = circ * (1 - pct / 100)
  return (
    <div className="relative size-28">
      <svg viewBox="0 0 100 100" className="size-28 -rotate-90" role="img" aria-label={label}>
        <title>{label}</title>
        <circle cx="50" cy="50" r={radius} fill="none" className="stroke-raised" strokeWidth="10" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          className="stroke-goal"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <p className="text-lg font-semibold leading-none">{value === null ? '—' : `${pct}%`}</p>
        <p className="mt-1 max-w-[5.5rem] text-[10px] leading-tight text-muted">{label}</p>
      </div>
    </div>
  )
}
