import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { AreaPage } from '@/pages/AreaPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { GoalPage } from '@/pages/GoalPage'
import { GoalsPage } from '@/pages/GoalsPage'
import { HabitPage } from '@/pages/HabitPage'
import { HomePage } from '@/pages/HomePage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'
import { WeekPage } from '@/pages/WeekPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="week" element={<WeekPage />} />
          <Route path="updates" element={<PlaceholderPage title="Updates" />} />
          <Route path="slips" element={<PlaceholderPage title="Slips" />} />
          <Route path="screen" element={<PlaceholderPage title="Screen Time" />} />
          <Route path="tasks" element={<PlaceholderPage title="Tasks" />} />
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
