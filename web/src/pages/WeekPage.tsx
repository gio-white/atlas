import { Navigate, useSearchParams } from 'react-router-dom'

export function WeekPage() {
  const [params] = useSearchParams()
  const next = new URLSearchParams(params)
  next.set('period', 'week')
  return <Navigate to={{ pathname: '/habit', search: next.toString() }} replace />
}
