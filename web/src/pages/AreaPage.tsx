import { useParams } from 'react-router-dom'

import { PlaceholderPage } from '@/components/PlaceholderPage'

export function AreaPage() {
  const { slug } = useParams()
  return (
    <PlaceholderPage
      title={slug ?? 'Area'}
      description="Metrics, habits, and goals for this area from GET /views/areas/{slug}."
    />
  )
}
