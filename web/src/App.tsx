import { lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { Redirect } from '@/components/shell/Redirect'
import { SectionLayout } from '@/components/shell/SectionLayout'
import { HabitsPage } from '@/pages/HabitsPage'
import { HealthPage } from '@/pages/HealthPage'
import { HomePage } from '@/pages/HomePage'
import { JournalPage } from '@/pages/JournalPage'
import { AppearancePage } from '@/pages/settings/AppearancePage'

// Home, Habits, and a few small pages are in the main bundle; every other page loads on first
// visit, in its own chunk (Layout and SectionLayout wrap pages in Suspense).
const DevicesPage = lazy(() =>
  import('@/pages/settings/DevicesPage').then((m) => ({ default: m.DevicesPage })),
)
const MetricsPage = lazy(() =>
  import('@/pages/settings/MetricsPage').then((m) => ({ default: m.MetricsPage })),
)
const ScreenTimeSetupPage = lazy(() =>
  import('@/pages/settings/ScreenTimeSetupPage').then((m) => ({
    default: m.ScreenTimeSetupPage,
  })),
)
const LibraryCategoryPage = lazy(() =>
  import('@/pages/LibraryCategoryPage').then((m) => ({
    default: m.LibraryCategoryPage,
  })),
)
const LibraryInsightsPage = lazy(() =>
  import('@/pages/LibraryInsightsPage').then((m) => ({
    default: m.LibraryInsightsPage,
  })),
)
const LibraryPage = lazy(() =>
  import('@/pages/LibraryPage').then((m) => ({ default: m.LibraryPage })),
)
const EntriesPage = lazy(() =>
  import('@/pages/EntriesPage').then((m) => ({ default: m.EntriesPage })),
)
const ScreenPage = lazy(() => import('@/pages/ScreenPage').then((m) => ({ default: m.ScreenPage })))
const ThisWeekPage = lazy(() =>
  import('@/pages/ThisWeekPage').then((m) => ({ default: m.ThisWeekPage })),
)
const SleepPage = lazy(() => import('@/pages/SleepPage').then((m) => ({ default: m.SleepPage })))
const AmbitionPage = lazy(() =>
  import('@/pages/quests/AmbitionPage').then((m) => ({ default: m.AmbitionPage })),
)
const PlanPage = lazy(() =>
  import('@/pages/quests/PlanPage').then((m) => ({ default: m.PlanPage })),
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

// Paths are written in full, also inside a section, so each one reads as the address it is
// and the docs drift test can match it against docs/product/navigation.md.
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="/journal" element={<JournalPage />} />

          <Route element={<SectionLayout section="quests" />}>
            <Route path="/quests" element={<MainQuestsPage />} />
            <Route path="/quests/side-quests" element={<SideQuestsPage />} />
            <Route path="/quests/inbox" element={<InboxPage />} />
            <Route path="/quests/plan" element={<PlanPage />} />
          </Route>
          <Route path="/quests/ambitions/:id" element={<AmbitionPage />} />
          <Route path="/quests/goals/:id" element={<GoalPage />} />
          <Route path="/quests/side-quests/:id" element={<SideQuestPage />} />

          <Route path="/habits" element={<HabitsPage />} />

          <Route path="/stats" element={<Redirect to="/stats/week" />} />
          <Route element={<SectionLayout section="stats" />}>
            <Route path="/stats/week" element={<ThisWeekPage />} />
            <Route path="/stats/sleep" element={<SleepPage />} />
            <Route path="/stats/screen-time" element={<ScreenPage />} />
            <Route path="/stats/health" element={<HealthPage />} />
          </Route>

          <Route path="/library" element={<LibraryPage />} />
          <Route path="/library/insights" element={<LibraryInsightsPage />} />
          <Route path="/library/:category" element={<LibraryCategoryPage />} />

          <Route path="/settings" element={<Redirect to="/settings/appearance" />} />
          <Route element={<SectionLayout section="settings" />}>
            <Route path="/settings/appearance" element={<AppearancePage />} />
            <Route path="/settings/screen-time" element={<ScreenTimeSetupPage />} />
            <Route path="/settings/devices" element={<DevicesPage />} />
            <Route path="/settings/metrics" element={<MetricsPage />} />
            <Route path="/settings/entries" element={<EntriesPage />} />
          </Route>

          {/* Addresses from before the rail. Each one lands on the page's new home. */}
          <Route path="/side-quests" element={<Redirect to="/quests/side-quests" />} />
          <Route path="/side-quests/:id" element={<Redirect to="/quests/side-quests/:id" />} />
          <Route path="/inbox" element={<Redirect to="/quests/inbox" />} />
          <Route path="/calendar" element={<Redirect to="/quests/plan" />} />
          <Route path="/sleep" element={<Redirect to="/stats/sleep" />} />
          <Route path="/screen" element={<Redirect to="/stats/screen-time" />} />
          <Route path="/health" element={<Redirect to="/stats/health" />} />
          <Route path="/today" element={<Redirect to="/" />} />
          <Route path="/adventure" element={<Redirect to="/" />} />
          <Route path="/entertainment/*" element={<Redirect to="/library/*" />} />
          <Route path="/history" element={<Redirect to="/settings/entries" />} />
          <Route path="/catalog" element={<Redirect to="/settings/metrics" />} />
          <Route path="/area/:slug" element={<Redirect to="/settings/metrics" />} />
          {/* The habits rebuild: the old Habits, habit, and Week pages, until their new screens. */}
          <Route path="/habit" element={<Redirect to="/habits" />} />
          <Route path="/habit/:slug" element={<Redirect to="/habits" />} />
          <Route path="/week" element={<Redirect to="/habits" />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
