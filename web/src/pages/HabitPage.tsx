import { useParams } from 'react-router-dom'

import { PlaceholderPage } from '@/components/PlaceholderPage'

export function HabitPage() {
  const { slug } = useParams()
  return (
    <PlaceholderPage
      title={slug ?? 'Habit'}
      description="Streak, adherence, and the current bucket from GET /habits/{slug}/status."
    />
  )
}
