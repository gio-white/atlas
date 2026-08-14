import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  EntertainmentCard,
  GoalsCard,
  LifeSectionCard,
  QuickAddCard,
  type QuickKind,
  QuoteCard,
  ScreenTimeCard,
  SlipsCard,
  TasksCard,
  TodaysFocusCard,
  UpdatesCard,
  WeeklyOverviewCard,
} from '@/components/home/HomeCards'
import { JournalDialog } from '@/components/JournalDialog'
import { PageError, PageLoading } from '@/components/PageState'
import {
  ApiError,
  createTask,
  type EntertainmentView,
  type Goal,
  getEntertainmentView,
  getHomeWeek,
  getScreenView,
  getSlips,
  getToday,
  getUpdates,
  type HomeWeek,
  listGoals,
  listMetrics,
  listTasks,
  logSlip,
  logUpdate,
  type Metric,
  type SlipsWeek,
  type TaskItem,
  type TodayView,
  type UpdatesStatus,
  updateTask,
} from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { greetingForHour } from '@/lib/greeting'
import { LIFE_SECTIONS } from '@/lib/sections'

function emptyToday(asOf: string): TodayView {
  return { as_of: asOf, habits: [], entries: [], goals: [] }
}

function loadError(caught: unknown): string {
  return caught instanceof ApiError ? caught.message : 'Could not load home'
}

export function HomePage() {
  const { asOf, displayName, openLog } = useShell()
  const navigate = useNavigate()
  const [view, setView] = useState<TodayView | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [screenMinutes, setScreenMinutes] = useState<number | null>(null)
  const [updates, setUpdates] = useState<UpdatesStatus | null>(null)
  const [slips, setSlips] = useState<SlipsWeek | null>(null)
  const [week, setWeek] = useState<HomeWeek | null>(null)
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [goals, setGoals] = useState<Goal[]>([])
  const [entertainment, setEntertainment] = useState<EntertainmentView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [journalOpen, setJournalOpen] = useState(false)
  const greeting = greetingForHour(new Date().getHours())

  const refresh = useCallback(async () => {
    const [
      todayResult,
      metricRows,
      screen,
      updateStatus,
      slipWeek,
      taskRows,
      homeWeek,
      goalRows,
      entertainmentView,
    ] = await Promise.all([
      getToday(asOf)
        .then((data) => ({ data, error: null as string | null }))
        .catch((caught: unknown) => ({ data: null, error: loadError(caught) })),
      listMetrics().catch(() => []),
      getScreenView(asOf).catch(() => null),
      getUpdates(asOf).catch(() => null),
      getSlips(asOf).catch(() => null),
      listTasks({ include_done: true }).catch(() => []),
      getHomeWeek(asOf).catch(() => null),
      listGoals().catch(() => []),
      getEntertainmentView(asOf).catch(() => null),
    ])
    setError(todayResult.error)
    setView(todayResult.data ?? emptyToday(asOf))
    setMetrics(metricRows)
    setScreenMinutes(screen?.judgments.total ?? null)
    setUpdates(updateStatus)
    setSlips(slipWeek)
    setTasks(taskRows)
    setWeek(homeWeek)
    setGoals(goalRows)
    setEntertainment(entertainmentView)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(loadError(caught))
        setView(emptyToday(asOf))
      }
    })
    return () => {
      cancelled = true
    }
  }, [asOf, refresh])

  if (view === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">
          Good {greeting}, {displayName}
        </h1>
        <p className="mt-1 text-sm text-muted">Focus on progress, not perfection.</p>
      </header>
      {error !== null && <PageError message={error} />}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <UpdatesCard
          streakDays={updates?.current_streak ?? 0}
          onAdd={() => {
            void logUpdate({ occurred_on: asOf }).then(() => refresh())
          }}
        />
        <SlipsCard view={slips} />
        <ScreenTimeCard minutes={screenMinutes} />
        <GoalsCard goals={view.goals} />
      </section>
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.4fr)]">
        <TodaysFocusCard
          habits={view.habits}
          metrics={metrics}
          asOf={asOf}
          onLogged={refresh}
          onOpenLog={openLog}
        />
        <TasksCard
          tasks={tasks}
          goals={goals}
          onAdd={async (title, bucket, goal) => {
            await createTask({ title, bucket, goal })
            await refresh()
          }}
          onToggle={async (id, done) => {
            await updateTask(id, { done })
            await refresh()
          }}
        />
        <WeeklyOverviewCard view={week} />
      </section>
      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <QuoteCard />
        <QuickAddCard
          onPick={(kind: QuickKind) => {
            if (kind === 'update') {
              void logUpdate({ occurred_on: asOf }).then(() => refresh())
              return
            }
            if (kind === 'slip') {
              void logSlip({ occurred_on: asOf }).then(() => refresh())
              return
            }
            if (kind === 'screen') {
              openLog()
              return
            }
            if (kind === 'task') {
              document.getElementById('home-task-title')?.focus()
              return
            }
            if (kind === 'goal') {
              void navigate('/goal')
              return
            }
            setJournalOpen(true)
          }}
        />
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {LIFE_SECTIONS.map((section) =>
          section.slug === 'entertainment' ? (
            <EntertainmentCard key={section.slug} section={section} view={entertainment} />
          ) : (
            <LifeSectionCard key={section.slug} section={section} />
          ),
        )}
      </section>
      <JournalDialog open={journalOpen} onOpenChange={setJournalOpen} occurredOn={asOf} />
    </div>
  )
}
