import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { currentTheme, setTheme, toggleTheme } from '@/lib/theme'

export function ThemeToggle() {
  const [theme, setThemeState] = useState(currentTheme)

  function onToggle() {
    const next = toggleTheme(theme)
    setTheme(next)
    setThemeState(next)
  }

  const toDark = theme === 'light'

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      aria-label={toDark ? 'Switch to dark mode' : 'Switch to light mode'}
      aria-pressed={!toDark}
      title={toDark ? 'Dark mode' : 'Light mode'}
      onClick={onToggle}
    >
      {toDark ? <Moon className="size-4" aria-hidden /> : <Sun className="size-4" aria-hidden />}
    </Button>
  )
}
