import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { AreaPage } from '@/pages/AreaPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { GoalPage } from '@/pages/GoalPage'
import { GoalsPage } from '@/pages/GoalsPage'
import { HabitPage } from '@/pages/HabitPage'
import { TodayPage } from '@/pages/TodayPage'
import { WeekPage } from '@/pages/WeekPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<TodayPage />} />
          <Route path="week" element={<WeekPage />} />
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
