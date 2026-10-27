import { Pencil, Trash2 } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useState } from 'react'

import { JUDGMENT_LABEL } from '@/components/screen/Charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  type Comparator,
  createScreenBudget,
  deleteScreenSession,
  listScreenBudgets,
  listScreenSessions,
  type Period,
  type ScreenApp,
  type ScreenBudget,
  type ScreenBudgetTargetKind,
  type ScreenCategory,
  type ScreenDevice,
  type ScreenSessionRecord,
  updateScreenBudget,
  updateScreenSession,
} from '@/lib/api'
import { formatMinutes } from '@/lib/format'
import {
  budgetIsActive,
  budgetSlug,
  budgetSummary,
  draftFromSession,
  type SessionDraft,
  sessionTimeLabel,
  sessionUpdateBody,
} from '@/lib/screenManage'

const JUDGMENTS = ['waste', 'neutral', 'useful'] as const

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError || caught instanceof Error ? caught.message : fallback
}

function capName(
  kind: ScreenBudgetTargetKind,
  target: string,
  categories: ScreenCategory[],
): string {
  const base =
    kind === 'judgment'
      ? target.charAt(0).toUpperCase() + target.slice(1)
      : (categories.find((row) => row.slug === target)?.name ?? target)
  return `${base} cap`
}

function targetName(budget: ScreenBudget, categories: ScreenCategory[]): string {
  if (budget.target_kind === 'judgment') {
    return JUDGMENT_LABEL[budget.target_slug as keyof typeof JUDGMENT_LABEL] ?? budget.target_slug
  }
  return categories.find((row) => row.slug === budget.target_slug)?.name ?? budget.target_slug
}

export function BudgetsCard({
  asOf,
  categories,
  onChanged,
}: {
  asOf: string
  categories: ScreenCategory[]
  onChanged: () => Promise<void>
}) {
  const [budgets, setBudgets] = useState<ScreenBudget[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null)

  const load = useCallback(async () => setBudgets(await listScreenBudgets()), [])

  useEffect(() => {
    load().catch((caught: unknown) => setError(message(caught, 'Could not load caps')))
  }, [load])

  async function run(action: () => Promise<unknown>, fallback: string): Promise<boolean> {
    setError(null)
    try {
      await action()
      await Promise.all([load(), onChanged()])
      return true
    } catch (caught) {
      setError(message(caught, fallback))
      return false
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">Caps</CardTitle>
          <CardDescription>Limits on a judgment (all waste) or on one category</CardDescription>
        </div>
      </CardHeader>
      {budgets === null ? (
        <p className="text-sm text-muted">{error ?? 'Loading…'}</p>
      ) : (
        <div className="flex flex-col gap-4">
          {budgets.length === 0 ? (
            <p className="text-sm text-muted">No caps yet.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-line">
              {budgets.map((budget) => {
                const active = budgetIsActive(budget, asOf)
                return (
                  <li key={budget.slug} className="flex flex-col gap-2 py-2 first:pt-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium text-ink">{budget.name}</span>
                      <span className="text-sm text-muted">
                        {targetName(budget, categories)} {budgetSummary(budget)}
                      </span>
                      <Badge tone={active ? 'good' : 'default'}>
                        {active ? 'active' : `ended ${budget.active_to ?? ''}`}
                      </Badge>
                      <div className="ml-auto flex gap-1">
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditing(editing === budget.slug ? null : budget.slug)}
                        >
                          Edit
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            run(
                              () =>
                                updateScreenBudget(budget.slug, {
                                  active_to: active ? asOf : null,
                                }),
                              'Could not update cap',
                            )
                          }
                        >
                          {active ? 'End' : 'Resume'}
                        </Button>
                      </div>
                    </div>
                    {editing === budget.slug && (
                      <BudgetEditForm
                        budget={budget}
                        onSave={async (body) => {
                          if (
                            await run(
                              () => updateScreenBudget(budget.slug, body),
                              'Could not save cap',
                            )
                          )
                            setEditing(null)
                        }}
                      />
                    )}
                  </li>
                )
              })}
            </ul>
          )}
          <BudgetCreateForm
            asOf={asOf}
            categories={categories}
            onCreate={(body) => run(() => createScreenBudget(body), 'Could not create cap')}
          />
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
        </div>
      )}
    </Card>
  )
}

function BudgetEditForm({
  budget,
  onSave,
}: {
  budget: ScreenBudget
  onSave: (body: { name: string; target_value: number; comparator: Comparator }) => Promise<void>
}) {
  const [name, setName] = useState(budget.name)
  const [minutes, setMinutes] = useState(String(budget.target_value))
  const [comparator, setComparator] = useState<Comparator>(budget.comparator)
  const id = `budget-${budget.slug}`

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void onSave({ name: name.trim() || budget.name, target_value: Number(minutes), comparator })
  }

  return (
    <form className="grid gap-2 sm:grid-cols-4" onSubmit={onSubmit}>
      <div className="flex flex-col gap-1">
        <Label htmlFor={`${id}-name`}>Name</Label>
        <Input id={`${id}-name`} value={name} onChange={(event) => setName(event.target.value)} />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor={`${id}-cmp`}>Rule</Label>
        <Select
          id={`${id}-cmp`}
          value={comparator}
          onChange={(event) => setComparator(event.target.value as Comparator)}
        >
          <option value="at_most">at most</option>
          <option value="at_least">at least</option>
          <option value="exactly">exactly</option>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor={`${id}-min`}>Minutes</Label>
        <Input
          id={`${id}-min`}
          type="number"
          min="1"
          step="1"
          required
          value={minutes}
          onChange={(event) => setMinutes(event.target.value)}
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" size="sm">
          Save
        </Button>
      </div>
    </form>
  )
}

function BudgetCreateForm({
  asOf,
  categories,
  onCreate,
}: {
  asOf: string
  categories: ScreenCategory[]
  onCreate: (body: Parameters<typeof createScreenBudget>[0]) => Promise<boolean>
}) {
  const [kind, setKind] = useState<ScreenBudgetTargetKind>('judgment')
  const [target, setTarget] = useState<string>('waste')
  const [period, setPeriod] = useState<Period>('day')
  const [minutes, setMinutes] = useState('90')
  const [pending, setPending] = useState(false)
  const options =
    kind === 'judgment'
      ? JUDGMENTS.map((slug) => ({ slug, name: JUDGMENT_LABEL[slug] }))
      : categories.map((row) => ({ slug: row.slug, name: row.name }))

  function onKind(next: ScreenBudgetTargetKind) {
    setKind(next)
    setTarget(next === 'judgment' ? 'waste' : (categories[0]?.slug ?? ''))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    await onCreate({
      slug: budgetSlug(target, period),
      name: capName(kind, target, categories),
      target_kind: kind,
      target_slug: target,
      period,
      target_value: Number(minutes),
      comparator: 'at_most',
      active_from: asOf,
    })
    setPending(false)
  }

  return (
    <form
      className="grid gap-2 border-t border-line pt-3 sm:grid-cols-5"
      onSubmit={onSubmit}
      aria-label="New cap"
    >
      <div className="flex flex-col gap-1">
        <Label htmlFor="cap-kind">Cap on</Label>
        <Select
          id="cap-kind"
          value={kind}
          onChange={(event) => onKind(event.target.value as ScreenBudgetTargetKind)}
        >
          <option value="judgment">Judgment</option>
          <option value="category" disabled={categories.length === 0}>
            Category
          </option>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="cap-target">Target</Label>
        <Select id="cap-target" value={target} onChange={(event) => setTarget(event.target.value)}>
          {options.map((row) => (
            <option key={row.slug} value={row.slug}>
              {row.name}
            </option>
          ))}
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="cap-period">Per</Label>
        <Select
          id="cap-period"
          value={period}
          onChange={(event) => setPeriod(event.target.value as Period)}
        >
          <option value="day">day</option>
          <option value="week">week</option>
          <option value="month">month</option>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="cap-minutes">At most (min)</Label>
        <Input
          id="cap-minutes"
          type="number"
          min="1"
          step="1"
          required
          value={minutes}
          onChange={(event) => setMinutes(event.target.value)}
        />
      </div>
      <div className="flex items-end">
        <Button type="submit" size="sm" disabled={pending || target === ''}>
          Add cap
        </Button>
      </div>
    </form>
  )
}

export function SessionsCard({
  day,
  onDayChange,
  apps,
  devices,
  onChanged,
}: {
  day: string
  onDayChange: (day: string) => void
  apps: ScreenApp[]
  devices: ScreenDevice[]
  onChanged: () => Promise<void>
}) {
  const [rows, setRows] = useState<ScreenSessionRecord[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => setRows(await listScreenSessions(day)), [day])

  useEffect(() => {
    load().catch((caught: unknown) => setError(message(caught, 'Could not load sessions')))
  }, [load])

  async function run(action: () => Promise<unknown>, fallback: string): Promise<boolean> {
    setError(null)
    try {
      await action()
      await Promise.all([load(), onChanged()])
      return true
    } catch (caught) {
      setError(message(caught, fallback))
      return false
    }
  }

  const appName = (slug: string) => apps.find((row) => row.slug === slug)?.name ?? slug
  const deviceName = (slug: string | null) =>
    slug === null ? 'Unknown' : (devices.find((row) => row.slug === slug)?.name ?? slug)

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">Sessions</CardTitle>
          <CardDescription>Fix or remove a logged session</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="sessions-day" className="sr-only">
            Day
          </Label>
          <Input
            id="sessions-day"
            type="date"
            className="w-40"
            value={day}
            onChange={(event) => event.target.value && onDayChange(event.target.value)}
          />
        </div>
      </CardHeader>
      {error !== null && (
        <p className="mb-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
      {rows === null ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted">No sessions on this day.</p>
      ) : (
        <ul className="flex flex-col divide-y divide-line">
          {rows.map((row) => (
            <SessionRow
              key={row.id}
              row={row}
              appName={appName(row.app)}
              deviceName={deviceName(row.device)}
              devices={devices}
              onSave={(body) => run(() => updateScreenSession(row.id, body), 'Could not save')}
              onDelete={() => run(() => deleteScreenSession(row.id), 'Could not delete')}
            />
          ))}
        </ul>
      )}
    </Card>
  )
}

function SessionRow({
  row,
  appName,
  deviceName,
  devices,
  onSave,
  onDelete,
}: {
  row: ScreenSessionRecord
  appName: string
  deviceName: string
  devices: ScreenDevice[]
  onSave: (body: ReturnType<typeof sessionUpdateBody>) => Promise<boolean>
  onDelete: () => Promise<boolean>
}) {
  const [draft, setDraft] = useState<SessionDraft | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const id = `session-${row.id}`

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (draft === null) return
    setFormError(null)
    let body: ReturnType<typeof sessionUpdateBody>
    try {
      body = sessionUpdateBody(row, draft)
    } catch (caught) {
      setFormError(message(caught, 'Invalid session'))
      return
    }
    if (Object.keys(body).length === 0 || (await onSave(body))) setDraft(null)
  }

  return (
    <li className="flex flex-col gap-2 py-2 first:pt-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="font-medium text-ink">{appName}</span>
        <span className="font-mono text-muted">{formatMinutes(row.minutes)}</span>
        <span className="text-muted">{sessionTimeLabel(row)}</span>
        <span className="text-muted">· {deviceName}</span>
        {row.note !== null && <span className="text-muted">· {row.note}</span>}
        <div className="ml-auto flex items-center gap-1">
          {confirming ? (
            <>
              <Button type="button" size="sm" variant="destructive" onClick={() => onDelete()}>
                Delete
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={() => setConfirming(false)}>
                Keep
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                aria-label={`Edit ${appName} session`}
                onClick={() => setDraft(draft === null ? draftFromSession(row) : null)}
              >
                <Pencil className="size-4" aria-hidden />
              </Button>
              <Button
                type="button"
                size="icon"
                variant="ghost"
                aria-label={`Delete ${appName} session`}
                onClick={() => setConfirming(true)}
              >
                <Trash2 className="size-4" aria-hidden />
              </Button>
            </>
          )}
        </div>
      </div>
      {draft !== null && (
        <form className="grid gap-2 sm:grid-cols-4" onSubmit={onSubmit}>
          {row.started_at !== null ? (
            <>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`${id}-from`}>From</Label>
                <Input
                  id={`${id}-from`}
                  type="datetime-local"
                  value={draft.started}
                  onChange={(event) => setDraft({ ...draft, started: event.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1">
                <Label htmlFor={`${id}-to`}>To</Label>
                <Input
                  id={`${id}-to`}
                  type="datetime-local"
                  value={draft.ended}
                  onChange={(event) => setDraft({ ...draft, ended: event.target.value })}
                />
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-minutes`}>Minutes</Label>
              <Input
                id={`${id}-minutes`}
                type="number"
                min="0.01"
                step="0.01"
                value={draft.minutes}
                onChange={(event) => setDraft({ ...draft, minutes: event.target.value })}
              />
            </div>
          )}
          <div className="flex flex-col gap-1">
            <Label htmlFor={`${id}-device`}>Device</Label>
            <Select
              id={`${id}-device`}
              value={draft.device}
              onChange={(event) => setDraft({ ...draft, device: event.target.value })}
            >
              <option value="">Unknown</option>
              {devices.map((device) => (
                <option key={device.slug} value={device.slug}>
                  {device.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor={`${id}-note`}>Note</Label>
            <Input
              id={`${id}-note`}
              value={draft.note}
              onChange={(event) => setDraft({ ...draft, note: event.target.value })}
            />
          </div>
          <div className="flex items-end gap-2">
            <Button type="submit" size="sm">
              Save
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setDraft(null)}>
              Cancel
            </Button>
          </div>
          {formError !== null && (
            <p className="text-sm text-bad sm:col-span-4" role="alert">
              {formError}
            </p>
          )}
        </form>
      )}
    </li>
  )
}
