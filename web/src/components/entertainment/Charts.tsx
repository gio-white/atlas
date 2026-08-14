import { cn } from '@/lib/utils'

const PALETTE = [
  { stroke: 'stroke-entertainment', swatch: 'bg-entertainment' },
  { stroke: 'stroke-update', swatch: 'bg-update' },
  { stroke: 'stroke-screen', swatch: 'bg-screen' },
  { stroke: 'stroke-goal', swatch: 'bg-goal' },
  { stroke: 'stroke-adventure', swatch: 'bg-adventure' },
  { stroke: 'stroke-warn', swatch: 'bg-warn' },
] as const

export type CountSlice = {
  slug: string
  name: string
  count: number
  stroke: string
  swatch: string
}

export function countSlices(rows: { slug: string; name: string; count: number }[]): CountSlice[] {
  return rows.map((row, index) => ({
    ...row,
    ...PALETTE[index % PALETTE.length],
  }))
}

export function CountDonut({ slices, label }: { slices: CountSlice[]; label: string }) {
  const total = slices.reduce((sum, slice) => sum + slice.count, 0)
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
            const length = (slice.count / total) * circ
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
          <li className="text-muted">Nothing finished in this period.</li>
        ) : (
          slices.map((slice) => (
            <li key={slice.slug} className="flex items-center gap-2">
              <span className={cn('size-2 rounded-full', slice.swatch)} />
              {slice.name} · {slice.count}
            </li>
          ))
        )}
      </ul>
    </div>
  )
}
