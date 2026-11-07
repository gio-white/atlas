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
  listScreenBudgets,
  type Period,
  type ScreenBudget,
  type ScreenBudgetTargetKind,
  type ScreenCategory,
  updateScreenBudget,
} from '@/lib/api'
import { budgetSlug, budgetState, budgetSummary } from '@/lib/screenManage'

const JUDGMENTS = ['waste', 'neutral', 'useful'] as const

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError || caught instanceof Error ? caught.message : fallback
}

const PERIOD_ADJECTIVE: Record<Period, string> = { day: 'daily', week: 'weekly', month: 'monthly' }

function capName(
  kind: ScreenBudgetTargetKind,
  target: string,
  period: Period,
  categories: ScreenCategory[],
): string {
  const base =
    kind === 'judgment'
      ? target.charAt(0).toUpperCase() + target.slice(1)
      : (categories.find((row) => row.slug === target)?.name ?? target)
  return `${base} ${PERIOD_ADJECTIVE[period]} cap`
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
          <CardDescription>Limits on all Bad apps, or on one category</CardDescription>
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
                const state = budgetState(budget, asOf)
                return (
                  <li key={budget.slug} className="flex flex-col gap-2 py-2 first:pt-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium text-ink">{budget.name}</span>
                      <span className="text-sm text-muted">
                        {targetName(budget, categories)} {budgetSummary(budget)}
                      </span>
                      <Badge tone={state.counting ? 'good' : 'default'}>{state.label}</Badge>
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
                                  active_to: state.open ? asOf : null,
                                }),
                              'Could not update cap',
                            )
                          }
                        >
                          {state.open ? 'End' : 'Resume'}
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
      name: capName(kind, target, period, categories),
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
