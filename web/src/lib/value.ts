import type { ValueType } from './api'

export function parseLogValue(
  valueType: ValueType,
  raw: string,
  boolValue = true,
): boolean | number | string | null {
  if (valueType === 'bool') return boolValue
  if (valueType === 'text') return raw
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const numeric = Number(trimmed)
  if (Number.isNaN(numeric)) {
    throw new Error('value must be a number')
  }
  return numeric
}

export function rawFromEntry(
  valueNum: number | null,
  valueBool: boolean | null,
  valueText: string | null,
): string {
  if (valueBool !== null) return valueBool ? 'true' : 'false'
  if (valueText !== null) return valueText
  if (valueNum !== null) return String(valueNum)
  return ''
}
