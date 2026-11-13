import { generatePath, Navigate, useLocation, useParams } from 'react-router-dom'

/**
 * Send an old address to its new one, keeping ids, the query string (so the "As of" date and
 * filters survive), and the hash. `to` may use the old route's params (`:id`, `*`).
 */
export function Redirect({ to }: { to: string }) {
  const params = useParams()
  const { search, hash } = useLocation()
  return <Navigate to={{ pathname: generatePath(to, params), search, hash }} replace />
}
