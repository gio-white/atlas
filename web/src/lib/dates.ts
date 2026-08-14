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

export function shortDateLabel(isoDate: string): string {
  return parseIsoDate(isoDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

export function shiftPeriodDate(
  isoDate: string,
  period: 'day' | 'week' | 'month',
  delta: number,
): string {
  const date = parseIsoDate(isoDate)
  if (period === 'day') date.setDate(date.getDate() + delta)
  else if (period === 'week') date.setDate(date.getDate() + delta * 7)
  else {
    const day = date.getDate()
    date.setDate(1)
    date.setMonth(date.getMonth() + delta)
    const last = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
    date.setDate(Math.min(day, last))
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
