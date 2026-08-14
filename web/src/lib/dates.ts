export function parseIsoDate(isoDate: string): Date {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function weekdayLabel(isoDate: string): string {
  return parseIsoDate(isoDate).toLocaleDateString('en-GB', { weekday: 'short' })
}

export function longDateLabel(isoDate: string): string {
  return parseIsoDate(isoDate).toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}
