export type Theme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'atlas-theme'

export function isTheme(value: string | null): value is Theme {
  return value === 'light' || value === 'dark'
}

export function resolveTheme(stored: string | null, prefersDark: boolean): Theme {
  return isTheme(stored) ? stored : prefersDark ? 'dark' : 'light'
}

export function toggleTheme(current: Theme): Theme {
  return current === 'dark' ? 'light' : 'dark'
}

export function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export function persistTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // private mode / disabled storage
  }
}

export function readStoredTheme(): string | null {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY)
  } catch {
    return null
  }
}

export function prefersDarkScheme(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function currentTheme(): Theme {
  return resolveTheme(readStoredTheme(), prefersDarkScheme())
}

export function setTheme(theme: Theme): void {
  applyTheme(theme)
  persistTheme(theme)
}
