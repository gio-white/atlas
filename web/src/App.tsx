import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { LIFE_SECTIONS } from '@/lib/sections'
import { AreaPage } from '@/pages/AreaPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { EntertainmentPage } from '@/pages/EntertainmentPage'
import { GoalPage } from '@/pages/GoalPage'
import { GoalsPage } from '@/pages/GoalsPage'
import { HabitPage } from '@/pages/HabitPage'
import { HomePage } from '@/pages/HomePage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { ScreenPage } from '@/pages/ScreenPage'
import { SectionPage } from '@/pages/SectionPage'
import { TasksPage } from '@/pages/TasksPage'
import { WeekPage } from '@/pages/WeekPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="week" element={<WeekPage />} />
          {LIFE_SECTIONS.filter((section) => section.slug !== 'entertainment').map((section) => (
            <Route
              key={section.slug}
              path={section.slug}
              element={<SectionPage title={section.label} description={section.description} />}
            />
          ))}
          <Route path="entertainment" element={<EntertainmentPage />} />
          <Route path="screen" element={<ScreenPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="journal" element={<PlaceholderPage title="Journal" />} />
          <Route path="area/:slug" element={<AreaPage />} />
          <Route path="habit/:slug" element={<HabitPage />} />
          <Route path="goal" element={<GoalsPage />} />
          <Route path="goal/:slug" element={<GoalPage />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
