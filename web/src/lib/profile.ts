export const DISPLAY_NAME_KEY = 'atlas-display-name'
export const DEFAULT_DISPLAY_NAME = 'Alex'

export function normalizeDisplayName(value: string): string {
  const trimmed = value.trim()
  return trimmed === '' ? DEFAULT_DISPLAY_NAME : trimmed
}

export function readDisplayName(): string {
  try {
    return normalizeDisplayName(localStorage.getItem(DISPLAY_NAME_KEY) ?? '')
  } catch {
    return DEFAULT_DISPLAY_NAME
  }
}

export function persistDisplayName(value: string): string {
  const name = normalizeDisplayName(value)
  try {
    localStorage.setItem(DISPLAY_NAME_KEY, name)
  } catch {
    // private mode / disabled storage
  }
  return name
}

export function initials(name: string): string {
  const parts = normalizeDisplayName(name).split(/\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '')
  return letters.join('') || 'A'
}
