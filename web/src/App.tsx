import { lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { LIFE_SECTIONS } from '@/lib/sections'
import { AreaPage } from '@/pages/AreaPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { EntertainmentCategoryPage } from '@/pages/EntertainmentCategoryPage'
import { EntertainmentInsightsPage } from '@/pages/EntertainmentInsightsPage'
import { EntertainmentPage } from '@/pages/EntertainmentPage'
import { EntriesPage } from '@/pages/EntriesPage'
import { HabitPage } from '@/pages/HabitPage'
import { HabitsPage } from '@/pages/HabitsPage'
import { HomePage } from '@/pages/HomePage'
import { JournalPage } from '@/pages/JournalPage'
import { CalendarPage } from '@/pages/quests/CalendarPage'
import { TodayPage } from '@/pages/quests/TodayPage'
import { ScreenPage } from '@/pages/ScreenPage'
import { SectionPage } from '@/pages/SectionPage'
import { SleepPage } from '@/pages/SleepPage'
import { WeekPage } from '@/pages/WeekPage'

// The quest screens load on first visit, in their own chunk (Layout wraps pages in Suspense).
const AmbitionPage = lazy(() =>
  import('@/pages/quests/AmbitionPage').then((m) => ({ default: m.AmbitionPage })),
)
const GoalPage = lazy(() =>
  import('@/pages/quests/GoalPage').then((m) => ({ default: m.GoalPage })),
)
const InboxPage = lazy(() =>
  import('@/pages/quests/InboxPage').then((m) => ({ default: m.InboxPage })),
)
const MainQuestsPage = lazy(() =>
  import('@/pages/quests/MainQuestsPage').then((m) => ({ default: m.MainQuestsPage })),
)
const SideQuestPage = lazy(() =>
  import('@/pages/quests/SideQuestPage').then((m) => ({ default: m.SideQuestPage })),
)
const SideQuestsPage = lazy(() =>
  import('@/pages/quests/SideQuestsPage').then((m) => ({ default: m.SideQuestsPage })),
)

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="week" element={<WeekPage />} />
          {LIFE_SECTIONS.filter(
            (section) => section.slug !== 'entertainment' && section.slug !== 'sleep',
          ).map((section) => (
            <Route
              key={section.slug}
              path={section.slug}
              element={<SectionPage title={section.label} description={section.description} />}
            />
          ))}
          <Route path="sleep" element={<SleepPage />} />
          <Route path="entertainment" element={<EntertainmentPage />} />
          <Route path="entertainment/insights" element={<EntertainmentInsightsPage />} />
          <Route path="entertainment/:category" element={<EntertainmentCategoryPage />} />
          <Route path="screen" element={<ScreenPage />} />
          <Route path="journal" element={<JournalPage />} />
          <Route path="area/:slug" element={<AreaPage />} />
          <Route path="habit" element={<HabitsPage />} />
          <Route path="habit/:slug" element={<HabitPage />} />
          <Route path="today" element={<TodayPage />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="quests" element={<MainQuestsPage />} />
          <Route path="quests/ambitions/:id" element={<AmbitionPage />} />
          <Route path="quests/goals/:id" element={<GoalPage />} />
          <Route path="side-quests" element={<SideQuestsPage />} />
          <Route path="side-quests/:id" element={<SideQuestPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="history" element={<EntriesPage />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
