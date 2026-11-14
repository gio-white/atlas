import { type FormEvent, useState } from 'react'

import { PageHeader } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useShell } from '@/lib/asOf'
import { currentTheme, setTheme, type Theme } from '@/lib/theme'
import { cn } from '@/lib/utils'

const THEMES: { id: Theme; label: string }[] = [
  { id: 'dark', label: 'Dark' },
  { id: 'light', label: 'Light' },
]

/** Settings → Appearance: the theme and the name Atlas greets you with. Both stay on this device. */
export function AppearancePage() {
  const { displayName, setDisplayName } = useShell()
  const [theme, setThemeState] = useState(currentTheme)
  const [draft, setDraft] = useState(displayName)
  const [saved, setSaved] = useState(false)

  function chooseTheme(next: Theme) {
    setTheme(next)
    setThemeState(next)
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    setDisplayName(draft)
    setSaved(true)
  }

  return (
    <div className="flex max-w-xl flex-col gap-5">
      <PageHeader tab title="Appearance" description="How Atlas looks and what it calls you." />
      <Card className="p-4">
        <fieldset className="flex flex-wrap items-center justify-between gap-3">
          <legend className="sr-only">Theme</legend>
          <p className="text-sm font-medium text-ink" aria-hidden>
            Theme
          </p>
          <div className="inline-flex gap-1 rounded-lg bg-raised p-1">
            {THEMES.map((option) => (
              <button
                key={option.id}
                type="button"
                aria-pressed={theme === option.id}
                className={cn(
                  'min-h-8 cursor-pointer rounded-md px-3 text-xs font-medium focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none',
                  theme === option.id
                    ? 'bg-surface text-ink shadow-sm'
                    : 'text-muted hover:text-ink',
                )}
                onClick={() => chooseTheme(option.id)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </fieldset>
      </Card>
      <Card className="p-4">
        <form className="flex flex-col gap-3" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="display-name">Your name</Label>
            <Input
              id="display-name"
              value={draft}
              autoComplete="nickname"
              onChange={(event) => {
                setDraft(event.target.value)
                setSaved(false)
              }}
            />
          </div>
          <div className="flex items-center gap-3">
            <Button type="submit">Save</Button>
            {saved && (
              <p className="text-sm text-muted" role="status">
                Saved
              </p>
            )}
          </div>
        </form>
      </Card>
    </div>
  )
}
