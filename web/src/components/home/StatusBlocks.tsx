import { Link } from 'react-router-dom'

import { QuestRing } from '@/components/quests/QuestVisuals'
import { Button } from '@/components/ui/button'
import type {
  EntertainmentTitle,
  MainQuests,
  QuestGoal,
  ScreenDashboard,
  SleepView,
  WeekSoFar,
} from '@/lib/api'
import { formatMinutes, formatPercent } from '@/lib/format'
import { formatTime } from '@/lib/timeBlocks'

import { BlockEmpty, HomeBlock } from './HomeBlock'

type BlockProps = { search: string; className?: string }

const MAIN_QUESTS_SHOWN = 5
const IN_PROGRESS_SHOWN = 3

/** Four numbers for Monday to now. The API computes each with its section's own rules. */
export function WeekSoFarBlock({
  week,
  search,
  className,
}: BlockProps & { week: WeekSoFar | null }) {
  const rows =
    week === null
      ? []
      : [
          {
            label: 'Sessions kept',
            value:
              week.sessions_total === 0 ? '—' : `${week.sessions_kept} of ${week.sessions_total}`,
          },
          { label: 'Habits kept', value: formatPercent(week.habits_kept_share) },
          { label: 'Sleep, average', value: formatMinutes(week.sleep_average_minutes) },
          {
            label: 'Screen score',
            value: week.screen_score === null ? '—' : String(week.screen_score),
          },
        ]
  return (
    <HomeBlock
      id="week"
      title="This week so far"
      action={{ label: 'This week', to: '/stats/week' }}
      search={search}
      unavailable={week === null}
      className={className}
    >
      <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-2 text-sm">
        {rows.map((row) => (
          <div key={row.label} className="contents">
            <dt className="text-muted">{row.label}</dt>
            <dd className="text-right font-semibold tabular-nums text-ink">{row.value}</dd>
          </div>
        ))}
      </dl>
    </HomeBlock>
  )
}

/** Active goals in the same order as Main quests: each ambition's goals, then independent ones. */
export function activeGoals(quests: MainQuests): QuestGoal[] {
  return [...quests.ambitions.flatMap((section) => section.goals), ...quests.independent_goals]
    .filter((goal) => goal.status === 'active' && goal.archived_at === null)
    .slice(0, MAIN_QUESTS_SHOWN)
}

export function MainQuestsBlock({
  quests,
  search,
  className,
}: BlockProps & { quests: MainQuests | null }) {
  const goals = quests === null ? [] : activeGoals(quests)
  return (
    <HomeBlock
      id="main-quests"
      title="Main quests"
      action={{ label: 'All quests', to: '/quests' }}
      search={search}
      unavailable={quests === null}
      className={className}
    >
      {goals.length === 0 ? (
        <div className="flex flex-wrap items-center gap-3">
          <BlockEmpty>No goals yet.</BlockEmpty>
          <Button asChild size="sm" variant="outline">
            <Link to={{ pathname: '/quests', search }}>Add a goal</Link>
          </Button>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {goals.map((goal) => (
            <li key={goal.id} className="flex items-center gap-3">
              <QuestRing value={goal.progress} size={40} />
              <div className="min-w-0 flex-1">
                <Link
                  to={{ pathname: `/quests/goals/${goal.id}`, search }}
                  className="block truncate text-sm font-medium text-ink hover:underline"
                >
                  {goal.title}
                </Link>
                {goal.next_action !== null && (
                  <p className="truncate text-xs text-muted">Next: {goal.next_action.title}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </HomeBlock>
  )
}

export function LastNightBlock({
  sleep,
  search,
  className,
}: BlockProps & { sleep: SleepView | null }) {
  const night = sleep?.night ?? null
  return (
    <HomeBlock
      id="last-night"
      title="Last night"
      to="/stats/sleep"
      search={search}
      unavailable={sleep === null}
      className={className}
    >
      {night === null ? (
        <BlockEmpty>No sleep data for last night.</BlockEmpty>
      ) : (
        <p className="text-sm text-muted">
          <span className="text-2xl font-semibold tracking-tight text-ink tabular-nums">
            {formatMinutes(night.asleep_minutes)}
          </span>{' '}
          <span className="tabular-nums">
            · {formatTime(night.started_at)} → {formatTime(night.ended_at)}
          </span>
        </p>
      )}
    </HomeBlock>
  )
}

/** Minutes of today's daily cap on all screen time, when one is set and active. */
export function dailyTotalCap(screen: ScreenDashboard): number | null {
  const cap = screen.budgets.find(
    (budget) => budget.target_kind === 'total' && budget.period === 'day' && budget.scheduled,
  )
  return cap === undefined ? null : cap.target_value
}

export function ScreenTodayBlock({
  screen,
  search,
  className,
}: BlockProps & { screen: ScreenDashboard | null }) {
  const cap = screen === null ? null : dailyTotalCap(screen)
  const total = screen?.total ?? null
  return (
    <HomeBlock
      id="screen-today"
      title="Screen time today"
      to="/stats/screen-time"
      search={search}
      unavailable={screen === null}
      className={className}
    >
      {total === null ? (
        <BlockEmpty>No screen time data yet today.</BlockEmpty>
      ) : (
        <p className="text-sm text-muted">
          <span
            className={`text-2xl font-semibold tracking-tight tabular-nums ${
              cap !== null && total > cap ? 'text-bad' : 'text-ink'
            }`}
          >
            {formatMinutes(total)}
          </span>
          {cap !== null && <> of {formatMinutes(cap)} cap</>}
        </p>
      )}
    </HomeBlock>
  )
}

export function InProgressBlock({
  titles,
  search,
  className,
}: BlockProps & { titles: EntertainmentTitle[] | null }) {
  const shown = (titles ?? []).slice(0, IN_PROGRESS_SHOWN)
  return (
    <HomeBlock
      id="in-progress"
      title="In progress"
      to="/library"
      search={search}
      unavailable={titles === null}
      className={className}
    >
      {titles !== null &&
        (titles.length === 0 ? (
          <BlockEmpty>Nothing in progress.</BlockEmpty>
        ) : (
          <div className="flex flex-col gap-1 text-sm">
            <p className="text-muted">
              {titles.length === 1 ? '1 title' : `${titles.length} titles`}
            </p>
            <ul className="flex flex-col gap-1">
              {shown.map((title) => (
                <li key={title.slug} className="truncate text-ink">
                  {title.name}
                </li>
              ))}
            </ul>
          </div>
        ))}
    </HomeBlock>
  )
}
