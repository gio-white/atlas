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
