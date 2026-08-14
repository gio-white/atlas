import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  GoalsCard,
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
  getHomeWeek,
  getScreenView,
  getSlips,
  getToday,
  getUpdates,
  type HomeWeek,
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
  const [error, setError] = useState<string | null>(null)
  const [journalOpen, setJournalOpen] = useState(false)
  const greeting = greetingForHour(new Date().getHours())

  const refresh = useCallback(async () => {
    const [today, metricRows, screen, updateStatus, slipWeek, taskRows, homeWeek] =
      await Promise.all([
        getToday(asOf),
        listMetrics(),
        getScreenView(asOf).catch(() => null),
        getUpdates(asOf),
        getSlips(asOf),
        listTasks({ include_done: true }),
        getHomeWeek(asOf),
      ])
    setView(today)
    setMetrics(metricRows)
    setScreenMinutes(screen?.judgments.total ?? null)
    setUpdates(updateStatus)
    setSlips(slipWeek)
    setTasks(taskRows)
    setWeek(homeWeek)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load home')
        setView(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  if (error !== null) return <PageError message={error} />
  if (view === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">
          Good {greeting}, {displayName}
        </h1>
        <p className="mt-1 text-sm text-muted">Focus on progress, not perfection.</p>
      </header>
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
          onAdd={async (title, bucket) => {
            await createTask({ title, bucket })
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
      <JournalDialog open={journalOpen} onOpenChange={setJournalOpen} occurredOn={asOf} />
    </div>
  )
}
