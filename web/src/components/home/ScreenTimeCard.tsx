import { Monitor } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Segmented } from '@/components/home/Segmented'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { ScreenDashboard } from '@/lib/api'
import { formatMinutes } from '@/lib/format'
import {
  elapsedDays,
  type ScreenRange,
  type ScreenSplit,
  screenHeadline,
  screenRows,
} from '@/lib/home'

const RANGES: { id: ScreenRange; label: string }[] = [
  { id: 'day', label: 'Today' },
  { id: 'week', label: 'Week avg' },
]

const SPLITS: { id: ScreenSplit; label: string }[] = [
  { id: 'category', label: 'Categories' },
  { id: 'device', label: 'Devices' },
  { id: 'app', label: 'Apps' },
]

const ROW_LIMIT = 6

export function ScreenTimeCard({
  day,
  week,
  search,
}: {
  day: ScreenDashboard | null
  week: ScreenDashboard | null
  search: string
}) {
  const [range, setRange] = useState<ScreenRange>('day')
  const [split, setSplit] = useState<ScreenSplit>('category')
  const dash = range === 'day' ? day : week
  const rows = screenRows(dash, split, range)
  const shown = rows.slice(0, ROW_LIMIT)
  const max = Math.max(...shown.map((row) => row.minutes), 1)
  const headline = screenHeadline(dash, range)
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Monitor className="size-4 text-screen" aria-hidden />
            Screen Time
          </CardTitle>
          <CardDescription>
            {range === 'day'
              ? 'Total for today'
              : `Daily average over ${week === null ? 'this week' : `${elapsedDays(week)} days this week`}`}
          </CardDescription>
        </div>
        <Link
          to={{ pathname: '/screen', search }}
          className="text-xs font-medium text-screen hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-3xl font-semibold tracking-tight">{formatMinutes(headline)}</p>
        <Segmented label="Screen time range" options={RANGES} value={range} onChange={setRange} />
      </div>
      <div className="mt-4">
        <Segmented
          label="Split screen time by"
          options={SPLITS}
          value={split}
          onChange={setSplit}
        />
      </div>
      {dash === null ? (
        <p className="mt-4 text-sm text-muted">Screen time is unavailable right now.</p>
      ) : shown.length === 0 ? (
        <p className="mt-4 text-sm text-muted">
          {range === 'day' ? 'No screen time logged today.' : 'No screen time logged this week.'}
        </p>
      ) : (
        <ul className="mt-4 flex flex-col gap-2.5">
          {shown.map((row) => (
            <li
              key={row.slug}
              className="grid grid-cols-[minmax(0,7rem)_minmax(0,1fr)_3.5rem] items-center gap-3 text-sm"
              title={`${row.name} · ${formatMinutes(row.minutes)}${range === 'week' ? ' / day' : ''}`}
            >
              <span className="truncate">{row.name}</span>
              <span className="h-2 rounded-full bg-raised">
                <span
                  className="block h-2 rounded-full bg-screen"
                  style={{ width: `${Math.max(3, (row.minutes / max) * 100)}%` }}
                />
              </span>
              <span className="text-right tabular-nums text-muted">
                {formatMinutes(row.minutes)}
              </span>
            </li>
          ))}
          {rows.length > ROW_LIMIT && (
            <li className="text-xs text-muted">+{rows.length - ROW_LIMIT} more on Screen Time</li>
          )}
        </ul>
      )}
    </Card>
  )
}
