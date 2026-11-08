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
import { AmbitionPage } from '@/pages/quests/AmbitionPage'
import { CalendarPage } from '@/pages/quests/CalendarPage'
import { GoalPage } from '@/pages/quests/GoalPage'
import { InboxPage } from '@/pages/quests/InboxPage'
import { MainQuestsPage } from '@/pages/quests/MainQuestsPage'
import { SideQuestPage } from '@/pages/quests/SideQuestPage'
import { SideQuestsPage } from '@/pages/quests/SideQuestsPage'
import { TodayPage } from '@/pages/quests/TodayPage'
import { ScreenPage } from '@/pages/ScreenPage'
import { SectionPage } from '@/pages/SectionPage'
import { SleepPage } from '@/pages/SleepPage'
import { WeekPage } from '@/pages/WeekPage'

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
