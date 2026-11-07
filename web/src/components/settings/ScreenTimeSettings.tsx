import { type FormEvent, type ReactNode, useCallback, useEffect, useState } from 'react'

import { JUDGMENT_LABEL } from '@/components/screen/Charts'
import { BudgetsCard } from '@/components/screen/ManageCards'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  createScreenApp,
  createScreenCategory,
  listScreenApps,
  listScreenCategories,
  type ScreenApp,
  type ScreenCategory,
  type ScreenJudgment,
  updateScreenApp,
  updateScreenCategory,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { isValidSlug } from '@/lib/slug'

const JUDGMENTS: ScreenJudgment[] = ['useful', 'neutral', 'waste']

export function slugFromName(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback
}

/**
 * Screen Time configuration: which categories count as Good, Bad, or Neutral, which category
 * each app belongs to, and caps. Self-contained (it loads its own data) so it can move into a
 * Settings page as one line; `onChanged` lets a host page refresh what it displays.
 */
export function ScreenTimeSettings({ onChanged }: { onChanged?: () => Promise<void> }) {
  const asOf = useAsOf()
  const [categories, setCategories] = useState<ScreenCategory[] | null>(null)
  const [apps, setApps] = useState<ScreenApp[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const [nextCategories, nextApps] = await Promise.all([listScreenCategories(), listScreenApps()])
    setCategories(nextCategories)
    setApps(nextApps)
  }, [])

  useEffect(() => {
    load().catch((caught: unknown) => setError(message(caught, 'Could not load settings')))
  }, [load])

  const changed = useCallback(async () => {
    await Promise.all([load(), onChanged?.()])
  }, [load, onChanged])

  if (categories === null) {
    return <p className="text-sm text-muted">{error ?? 'Loading…'}</p>
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <TaxonomyCard
          title="Categories"
          description="Whether time in each category counts as Good, Bad, or Neutral"
          noun="category"
          extra={{
            label: 'Counts as',
            options: JUDGMENTS.map((value) => ({ value, label: JUDGMENT_LABEL[value] })),
          }}
          onCreate={async (name, judgment) => {
            await createScreenCategory({
              slug: slugFromName(name),
              name,
              judgment: judgment as ScreenJudgment,
            })
            await changed()
          }}
          rows={categories.map((row) => (
            <EditableRow
              key={row.slug}
              name={row.name}
              label={`${row.name} counts as`}
              value={row.judgment}
              options={JUDGMENTS.map((value) => ({ value, label: JUDGMENT_LABEL[value] }))}
              onChange={async (judgment) => {
                await updateScreenCategory(row.slug, { judgment: judgment as ScreenJudgment })
                await changed()
              }}
            />
          ))}
        />
        <TaxonomyCard
          title="Apps"
          description="Which category each app belongs to"
          noun="app"
          extra={{
            label: 'Category',
            options: categories.map((row) => ({ value: row.slug, label: row.name })),
          }}
          onCreate={async (name, category) => {
            await createScreenApp({ slug: slugFromName(name), name, category })
            await changed()
          }}
          rows={apps.map((row) => (
            <EditableRow
              key={row.slug}
              name={row.name}
              label={`${row.name} category`}
              value={row.category}
              options={categories.map((category) => ({
                value: category.slug,
                label: category.name,
              }))}
              onChange={async (category) => {
                await updateScreenApp(row.slug, { category })
                await changed()
              }}
            />
          ))}
        />
      </div>
      <BudgetsCard asOf={asOf} categories={categories} onChanged={changed} />
    </div>
  )
}

export function TaxonomyCard({
  title,
  description,
  noun,
  extra,
  onCreate,
  rows,
}: {
  title: string
  description: string
  noun: string
  extra?: { label: string; options: { value: string; label: string }[] }
  onCreate: (name: string, extra: string) => Promise<void>
  rows: ReactNode[]
}) {
  const [name, setName] = useState('')
  const [choice, setChoice] = useState('')
  const [error, setError] = useState<string | null>(null)
  const extraValue = extra === undefined ? '' : choice || (extra.options[0]?.value ?? '')
  const canSubmit = isValidSlug(slugFromName(name)) && (extra === undefined || extraValue !== '')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await onCreate(name.trim(), extraValue)
      setName('')
    } catch (caught: unknown) {
      setError(message(caught, `Could not add the ${noun}`))
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      {rows.length === 0 ? (
        <p className="mb-3 text-sm text-muted">None yet.</p>
      ) : (
        <ul className="mb-3 flex max-h-56 flex-col gap-1.5 overflow-auto pr-1 text-sm">{rows}</ul>
      )}
      <form className="flex flex-wrap items-center gap-2" onSubmit={onSubmit}>
        <Input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder={`New ${noun} name`}
          aria-label={`New ${noun} name`}
          className="min-w-40 flex-1"
        />
        {extra !== undefined && (
          <Select
            value={extraValue}
            onChange={(event) => setChoice(event.target.value)}
            aria-label={`New ${noun} ${extra.label.toLowerCase()}`}
            className="w-36"
          >
            {extra.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        )}
        <Button type="submit" size="sm" disabled={!canSubmit}>
          Add {noun}
        </Button>
      </form>
      {error !== null && (
        <p className="mt-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
  )
}

function EditableRow({
  name,
  label,
  value,
  options,
  onChange,
}: {
  name: string
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (value: string) => Promise<void>
}) {
  const [error, setError] = useState<string | null>(null)
  return (
    <li className="flex flex-col gap-0.5">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-ink">{name}</span>
        <Select
          aria-label={label}
          className="h-8 w-36 text-xs"
          value={value}
          onChange={(event) => {
            setError(null)
            onChange(event.target.value).catch((caught: unknown) => {
              setError(message(caught, 'Could not save'))
            })
          }}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>
      {error !== null && (
        <span className="text-xs text-bad" role="alert">
          {error}
        </span>
      )}
    </li>
  )
}
