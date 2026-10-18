import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { HabitsWeekCard, TasksCard } from '@/components/home/HomeCards'
import { ScreenTimeCard } from '@/components/home/ScreenTimeCard'
import { SleepCard } from '@/components/home/SleepCard'
import { PageLoading } from '@/components/PageState'
import {
  createTask,
  type Goal,
  getHabitsCalendar,
  getScreenDashboard,
  getSleepView,
  type HabitsCalendar,
  listGoals,
  listMetrics,
  listTasks,
  type Metric,
  type ScreenDashboard,
  type SleepView,
  type TaskItem,
  updateTask,
} from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import { greetingForHour } from '@/lib/greeting'

type HomeData = {
  sleep: SleepView | null
  screenDay: ScreenDashboard | null
  screenWeek: ScreenDashboard | null
  tasks: TaskItem[]
  goals: Goal[]
  habits: HabitsCalendar | null
  metrics: Metric[]
}

async function loadHome(asOf: string): Promise<HomeData> {
  const [sleep, screenDay, screenWeek, tasks, goals, habits, metrics] = await Promise.all([
    getSleepView(asOf).catch(() => null),
    getScreenDashboard('day', asOf).catch(() => null),
    getScreenDashboard('week', asOf).catch(() => null),
    listTasks({ include_done: true }).catch(() => []),
    listGoals({ status: 'active' }).catch(() => []),
    getHabitsCalendar('week', asOf).catch(() => null),
    listMetrics().catch(() => []),
  ])
  return { sleep, screenDay, screenWeek, tasks, goals, habits, metrics }
}

export function HomePage() {
  const { asOf, displayName } = useShell()
  const [params] = useSearchParams()
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const [data, setData] = useState<HomeData | null>(null)
  const greeting = greetingForHour(new Date().getHours())

  const refresh = useCallback(async () => {
    setData(await loadHome(asOf))
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    void loadHome(asOf).then((next) => {
      if (!cancelled) setData(next)
    })
    return () => {
      cancelled = true
    }
  }, [asOf])

  if (data === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">
          Good {greeting}, {displayName}
        </h1>
        <p className="mt-1 text-sm text-muted">{longDateLabel(asOf)}</p>
      </header>
      <section
        aria-label="Overview"
        className="grid grid-cols-[minmax(0,1fr)] gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]"
      >
        <SleepCard view={data.sleep} asOf={asOf} onLogged={refresh} />
        <ScreenTimeCard day={data.screenDay} week={data.screenWeek} search={search} />
      </section>
      <section
        aria-label="Today"
        className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]"
      >
        <TasksCard
          tasks={data.tasks}
          goals={data.goals}
          asOf={asOf}
          search={search}
          onAdd={async (title, bucket, goal) => {
            await createTask({ title, bucket, goal })
            await refresh()
          }}
          onToggle={async (id, done) => {
            await updateTask(id, { done })
            await refresh()
          }}
        />
        <HabitsWeekCard
          calendar={data.habits}
          metrics={data.metrics}
          asOf={asOf}
          search={search}
          onChanged={refresh}
        />
      </section>
    </div>
  )
}
