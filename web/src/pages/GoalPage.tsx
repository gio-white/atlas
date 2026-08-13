import { useParams } from 'react-router-dom'

import { PlaceholderPage } from '@/components/PlaceholderPage'

export function GoalPage() {
  const { slug } = useParams()
  return (
    <PlaceholderPage
      title={slug ?? 'Goal'}
      description="Progress, pace, and milestone toggles for this goal."
    />
  )
}
