import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { HabitsTodayBlock } from '@/components/home/HabitsTodayBlock'
import { NoteBlock } from '@/components/home/NoteBlock'
import {
  DueTodayBlock,
  ToConfirmBlock,
  TodayBlock,
  UpNextBlock,
} from '@/components/home/QuestBlocks'
import {
  InProgressBlock,
  LastNightBlock,
  MainQuestsBlock,
  ScreenTodayBlock,
  WeekSoFarBlock,
} from '@/components/home/StatusBlocks'
import { PageError, PageLoading } from '@/components/PageState'
import { type DialogTask, TimeBlockDialog } from '@/components/quests/time/TimeBlockDialog'
import { useSessionActions } from '@/components/quests/time/useSessionActions'
import {
  getHabitsBoard,
  getJournal,
  getMainQuests,
  getScreenDashboard,
  getSleepView,
  getTodayQuests,
  getWeekSoFar,
  type HabitsBoard,
  type JournalDay,
  type LibraryTitle,
  listLibraryTitles,
  type MainQuests,
  type ScreenDashboard,
  type SleepView,
  type TodayQuests,
  type WeekSoFar,
} from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { greetingForHour } from '@/lib/greeting'

/** Every source Home reads. A source that fails is null, and only its blocks say so. */
export type HomeData = {
  today: TodayQuests | null
  habits: HabitsBoard | null
  journal: JournalDay | null
  week: WeekSoFar | null
  quests: MainQuests | null
  sleep: SleepView | null
  screen: ScreenDashboard | null
  reading: LibraryTitle[] | null
}

export async function loadHome(asOf: string): Promise<HomeData> {
  const [today, habits, journal, week, quests, sleep, screen, reading] = await Promise.all([
    getTodayQuests(asOf).catch(() => null),
    getHabitsBoard(asOf).catch(() => null),
    getJournal(asOf).catch(() => null),
    getWeekSoFar(asOf).catch(() => null),
    getMainQuests().catch(() => null),
    getSleepView(asOf).catch(() => null),
    getScreenDashboard('day', asOf).catch(() => null),
    listLibraryTitles({ status: 'in_progress' }).catch(() => null),
  ])
  return { today, habits, journal, week, quests, sleep, screen, reading }
}

/**
 * Home: the single daily entry point. Left, what to do today; right, where you stand, each
 * block a doorway into its section. On narrow screens the two columns become one, in the order
 * of the redesign brief: the `order-*` classes only apply there, because each column is
 * `display: contents` until `lg`, so its blocks join one flex list.
 */
export function HomePage() {
  const { asOf, displayName } = useShell()
  const [params] = useSearchParams()
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const [data, setData] = useState<HomeData | null>(null)
  const [scheduling, setScheduling] = useState<{ task: DialogTask | null } | null>(null)
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

  const { actions, status, error, dialogs } = useSessionActions(refresh)

  if (data === null) return <PageLoading />

  const schedule = (task: DialogTask | null) => setScheduling({ task })

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Good {greeting}, {displayName}
      </h1>

      <div aria-live="polite" className="empty:hidden">
        {status !== null && (
          <p className="rounded-xl border border-good/30 bg-good/10 px-4 py-2 text-sm text-good">
            {status}
          </p>
        )}
      </div>
      {error !== null && <PageError message={error} />}

      <div className="flex flex-col gap-5 lg:grid lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] lg:items-start">
        <div className="contents lg:flex lg:flex-col lg:gap-5">
          <ToConfirmBlock
            today={data.today}
            search={search}
            actions={actions}
            className="order-1 lg:order-none"
          />
          <TodayBlock
            today={data.today}
            search={search}
            actions={actions}
            onPlan={() => schedule(null)}
            className="order-2 lg:order-none"
          />
          <DueTodayBlock
            today={data.today}
            search={search}
            onSchedule={schedule}
            className="order-3 lg:order-none"
          />
          <UpNextBlock
            today={data.today}
            search={search}
            onSchedule={schedule}
            className="order-5 lg:order-none"
          />
          <HabitsTodayBlock
            board={data.habits}
            asOf={asOf}
            search={search}
            onChanged={refresh}
            className="order-4 lg:order-none"
          />
          <NoteBlock
            journal={data.journal}
            asOf={asOf}
            search={search}
            onSaved={refresh}
            className="order-6 lg:order-none"
          />
        </div>
        <div className="contents lg:flex lg:flex-col lg:gap-5">
          <WeekSoFarBlock week={data.week} search={search} className="order-7 lg:order-none" />
          <MainQuestsBlock quests={data.quests} search={search} className="order-8 lg:order-none" />
          <LastNightBlock sleep={data.sleep} search={search} className="order-9 lg:order-none" />
          <ScreenTodayBlock
            screen={data.screen}
            search={search}
            className="order-10 lg:order-none"
          />
          <InProgressBlock
            titles={data.reading}
            search={search}
            className="order-11 lg:order-none"
          />
        </div>
      </div>

      {dialogs}
      <TimeBlockDialog
        open={scheduling !== null}
        onOpenChange={(open) => !open && setScheduling(null)}
        task={scheduling?.task}
        onSaved={refresh}
      />
    </div>
  )
}
