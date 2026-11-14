import type { SleepNight, SleepStageMinutes, SleepView } from '@/lib/api'
import { shortDateLabel, weekdayLabel } from '@/lib/dates'
import { formatMinutes } from '@/lib/format'
import {
  asleepAxis,
  formatClock,
  SLEEP_STAGE_META,
  SLEEP_STAGES,
  stageShares,
  weekAxis,
} from '@/lib/sleep'
import { cn } from '@/lib/utils'

const NO_DATA = 'No data'

/** Room above the plot so the top tick label is never clipped by the viewBox. */
const PAD_TOP = 8
const FOOT = 16

function dayLabel(date: string, count: number): string {
  return count <= 7 ? weekdayLabel(date).slice(0, 2) : shortDateLabel(date)
}

/** Which day columns get an x-axis label: every day for a week, then spaced from the newest. */
function labelled(index: number, count: number): boolean {
  if (count <= 7) return true
  const step = count <= 31 ? 5 : 15
  return (count - 1 - index) % step === 0
}

/** Centre a day label under its column, but pin it inside the right edge so it is not cut. */
function axisLabelPosition(cx: number, width: number): { x: number; textAnchor: 'middle' | 'end' } {
  return cx + 18 > width ? { x: width, textAnchor: 'end' } : { x: cx, textAnchor: 'middle' }
}

function GapColumn({
  x,
  width,
  top,
  height,
  date,
  showText,
}: {
  x: number
  width: number
  top: number
  height: number
  date: string
  showText: boolean
}) {
  return (
    <g data-testid="sleep-gap">
      <title>
        {shortDateLabel(date)} · {NO_DATA}
      </title>
      <rect
        x={x}
        y={top}
        width={width}
        height={height}
        rx="3"
        className="fill-raised stroke-line"
        strokeDasharray="3 3"
        strokeWidth="1"
      />
      {showText && (
        <text
          x={x + width / 2}
          y={top + height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          className="fill-muted text-[9px]"
        >
          {NO_DATA}
        </text>
      )}
    </g>
  )
}

export function GapLegend() {
  return (
    <span className="flex items-center gap-1.5">
      <span className="size-2 rounded-sm border border-dashed border-muted bg-raised" aria-hidden />
      {NO_DATA}
    </span>
  )
}

export function StageLegend({ withGap = false }: { withGap?: boolean }) {
  return (
    <ul className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted" aria-label="Stages">
      {SLEEP_STAGES.map((stage) => (
        <li key={stage} className="flex items-center gap-1.5">
          <span className={cn('size-2 rounded-sm', SLEEP_STAGE_META[stage].bg)} aria-hidden />
          {SLEEP_STAGE_META[stage].label}
        </li>
      ))}
      {withGap && (
        <li>
          <GapLegend />
        </li>
      )}
    </ul>
  )
}

const HYPNO_STAGES = ['awake', 'rem', 'light', 'deep'] as const
const HYPNO_WIDTH = 300
const HYPNO_LABEL = 40
const HYPNO_LANE = 14
const HYPNO_GAP = 4

export function Hypnogram({ night }: { night: SleepNight }) {
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

/**
 * Bedtime-to-wake bars, one column per day, on a clock axis. A night with stages is coloured
 * by stage; without stages it is a single sleep-coloured bar. Days without a night are dashed
 * "No data" columns, so a gap is never a silent blank.
 */
export function NightsChart({
  view,
  width = 300,
  height = 170,
  showAverages = false,
}: {
  view: SleepView
  width?: number
  height?: number
  showAverages?: boolean
}) {
  const axisWidth = 34
  const axis = weekAxis(view)
  const count = view.days.length
  const plotHeight = height - FOOT - PAD_TOP
  const column = (width - axisWidth) / Math.max(1, count)
  const barWidth = Math.max(1.5, Math.min(18, column * 0.6))
  const y = (offset: number) =>
    PAD_TOP + ((offset - axis.start) / (axis.end - axis.start)) * plotHeight
  const label = `Bedtime and wake time, ${count} days`
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label={label}>
      <title>{label}</title>
      {axis.ticks.map((tick) => (
        <g key={tick}>
          <line
            x1={axisWidth}
            x2={width}
            y1={y(tick)}
            y2={y(tick)}
            className="stroke-line"
            strokeWidth="1"
          />
          <text
            x="0"
            y={y(tick)}
            dominantBaseline="middle"
            className="fill-muted text-[10px] tabular-nums"
          >
            {formatClock(tick)}
          </text>
        </g>
      ))}
      {showAverages &&
        [view.average_bed_offset, view.average_wake_offset].map((offset, index) =>
          offset === null ? null : (
            <line
              key={index === 0 ? 'bed' : 'wake'}
              x1={axisWidth}
              x2={width}
              y1={y(offset)}
              y2={y(offset)}
              className="stroke-muted"
              strokeWidth="1"
              strokeDasharray="4 3"
            >
              <title>
                {index === 0 ? 'Average bedtime' : 'Average wake'} {formatClock(offset)}
              </title>
            </line>
          ),
        )}
      {view.days.map((day, index) => {
        const cx = axisWidth + column * index + column / 2
        const night = day.night
        return (
          <g key={day.date}>
            {labelled(index, count) && (
              <text
                {...axisLabelPosition(cx, width)}
                y={height - 2}
                className={cn('text-[10px]', index === count - 1 ? 'fill-ink' : 'fill-muted')}
              >
                {dayLabel(day.date, count)}
              </text>
            )}
            {night === null ? (
              <GapColumn
                x={cx - barWidth / 2}
                width={barWidth}
                top={PAD_TOP}
                height={plotHeight}
                date={day.date}
                showText={false}
              />
            ) : (
              <NightBar night={night} cx={cx} barWidth={barWidth} y={y} date={day.date} />
            )}
          </g>
        )
      })}
    </svg>
  )
}

function NightBar({
  night,
  cx,
  barWidth,
  y,
  date,
}: {
  night: SleepNight
  cx: number
  barWidth: number
  y: (offset: number) => number
  date: string
}) {
  const top = y(night.bed_offset)
  const barHeight = Math.max(2, y(night.wake_offset) - top)
  const rx = Math.min(4, barWidth / 2)
  return (
    <g>
      <title>
        {weekdayLabel(date)} {shortDateLabel(date)} · {formatClock(night.bed_offset)} →{' '}
        {formatClock(night.wake_offset)} · {formatMinutes(night.asleep_minutes)} asleep
      </title>
      {night.segments.length === 0 ? (
        <rect
          x={cx - barWidth / 2}
          y={top}
          width={barWidth}
          height={barHeight}
          rx={rx}
          className="fill-data-neutral"
        />
      ) : (
        <>
          <clipPath id={`night-${date}`}>
            <rect x={cx - barWidth / 2} y={top} width={barWidth} height={barHeight} rx={rx} />
          </clipPath>
          <g clipPath={`url(#night-${date})`}>
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
    </g>
  )
}

/** Time asleep per day as bars from zero, with the window average as a dashed line. */
export function AsleepTrend({
  view,
  width = 640,
  height = 180,
}: {
  view: SleepView
  width?: number
  height?: number
}) {
  const axisWidth = 30
  const { max, ticks } = asleepAxis(view)
  const count = view.days.length
  const plotHeight = height - FOOT - PAD_TOP
  const column = (width - axisWidth) / Math.max(1, count)
  const barWidth = Math.max(1.5, Math.min(28, column * 0.65))
  const y = (minutes: number) => PAD_TOP + plotHeight - (minutes / max) * plotHeight
  const label = `Time asleep, ${count} days`
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label={label}>
      <title>{label}</title>
      {ticks.map((tick) => (
        <g key={tick}>
          <line
            x1={axisWidth}
            x2={width}
            y1={y(tick)}
            y2={y(tick)}
            className="stroke-line"
            strokeWidth="1"
          />
          <text
            x="0"
            y={y(tick)}
            dominantBaseline="middle"
            className="fill-muted text-[10px] tabular-nums"
          >
            {tick / 60}h
          </text>
        </g>
      ))}
      {view.days.map((day, index) => {
        const cx = axisWidth + column * index + column / 2
        const night = day.night
        return (
          <g key={day.date}>
            {labelled(index, count) && (
              <text
                {...axisLabelPosition(cx, width)}
                y={height - 2}
                className={cn('text-[10px]', index === count - 1 ? 'fill-ink' : 'fill-muted')}
              >
                {dayLabel(day.date, count)}
              </text>
            )}
            {night === null ? (
              <GapColumn
                x={cx - barWidth / 2}
                width={barWidth}
                top={PAD_TOP + plotHeight * 0.55}
                height={plotHeight * 0.45}
                date={day.date}
                showText={count <= 7}
              />
            ) : (
              <rect
                x={cx - barWidth / 2}
                y={y(night.asleep_minutes)}
                width={barWidth}
                height={Math.max(1, PAD_TOP + plotHeight - y(night.asleep_minutes))}
                rx={Math.min(4, barWidth / 2)}
                className="fill-series-1"
              >
                <title>
                  {weekdayLabel(day.date)} {shortDateLabel(day.date)} ·{' '}
                  {formatMinutes(night.asleep_minutes)} asleep
                </title>
              </rect>
            )}
          </g>
        )
      })}
      {view.average_asleep !== null && (
        <line
          x1={axisWidth}
          x2={width}
          y1={y(view.average_asleep)}
          y2={y(view.average_asleep)}
          className="stroke-ink"
          strokeOpacity="0.5"
          strokeWidth="1"
          strokeDasharray="4 3"
        >
          <title>Average {formatMinutes(view.average_asleep)}</title>
        </line>
      )}
    </svg>
  )
}

/** One stacked bar of the average stage minutes, then the share of each stage. */
export function StageSplit({ stages }: { stages: SleepStageMinutes }) {
  const shares = stageShares(stages)
  return (
    <div className="flex flex-col gap-3">
      <div className="flex h-3 overflow-hidden rounded-full bg-raised" aria-hidden>
        {shares.map((item) => (
          <span
            key={item.stage}
            className={cn('h-full', SLEEP_STAGE_META[item.stage].bg)}
            style={{ width: `${item.share * 100}%` }}
          />
        ))}
      </div>
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
    </div>
  )
}
