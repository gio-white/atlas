import { Link, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function PageHeader({
  title,
  kicker,
  description,
  homeLink = false,
}: {
  title: string
  kicker?: string
  description?: string
  homeLink?: boolean
}) {
  return (
    <header className="flex flex-col gap-1">
      {homeLink && <HomeLink />}
      {kicker !== undefined && <p className="font-mono text-xs text-muted">{kicker}</p>}
      <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
      {description !== undefined && <p className="text-sm text-muted">{description}</p>}
    </header>
  )
}

export function HomeLink() {
  const [params] = useSearchParams()
  return (
    <Link
      to={{ pathname: '/', search: params.toString() }}
      className="text-sm text-muted hover:text-ink"
    >
      Home
    </Link>
  )
}

export function PageLoading() {
  return (
    <div className="flex flex-col gap-3" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">Loading</span>
      <div className="h-8 w-40 animate-pulse rounded-lg bg-raised" />
      <div className="h-28 animate-pulse rounded-2xl bg-raised" />
      <div className="h-28 animate-pulse rounded-2xl bg-raised" />
    </div>
  )
}

export function PageError({ message }: { message: string }) {
  return (
    <p
      className="rounded-xl border border-bad/30 bg-bad/10 px-4 py-3 text-sm text-bad"
      role="alert"
    >
      {message}
    </p>
  )
}

export function PageUnavailable({
  title,
  description,
  message,
}: {
  title: string
  description?: string
  message: string
}) {
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={title} description={description} homeLink />
      <PageError message={message} />
    </div>
  )
}

export function EmptyState({
  title,
  hint,
  actionLabel,
  actionTo,
}: {
  title: string
  hint?: string
  actionLabel?: string
  actionTo?: string
}) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-raised/70 px-4 py-8 text-center">
      <p className="font-medium text-ink">{title}</p>
      {hint !== undefined && <p className="mt-1 text-sm text-muted">{hint}</p>}
      {actionLabel !== undefined && actionTo !== undefined && (
        <Button asChild size="sm" className="mt-3">
          <Link to={actionTo}>{actionLabel}</Link>
        </Button>
      )}
    </div>
  )
}

export function ProgressBar({ value }: { value: number | null }) {
  const pct = value === null ? 0 : Math.round(Math.min(1, Math.max(0, value)) * 100)
  return (
    <div
      className="h-1.5 overflow-hidden rounded-full bg-raised"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value === null ? undefined : pct}
    >
      <div
        className="h-full rounded-full bg-accent motion-safe:transition-[width] motion-safe:duration-200"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
