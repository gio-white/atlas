/**
 * The words people see for values the API names in code terms (docs/product/ux-writing.md).
 * A raw value such as `higher_is_better` never reaches the screen; it goes through a map here.
 */
import type { Aggregation, Direction, Metric, ValueType } from './api'

export const VALUE_TYPE_LABEL: Record<ValueType, string> = {
  bool: 'Yes / no',
  count: 'Count',
  quantity: 'Measurement',
  duration: 'Time spent',
  rating: 'Rating, 1 to 10',
  text: 'Note',
}

export const AGGREGATION_LABEL: Record<Aggregation, string> = {
  sum: 'Add up the day',
  last: 'Keep the latest',
  mean: 'Average the day',
  max: 'Keep the highest',
  min: 'Keep the lowest',
}

export const DIRECTION_LABEL: Record<Direction, string> = {
  higher_is_better: 'More is better',
  lower_is_better: 'Less is better',
  neutral: 'Neither',
}

export const VALUE_TYPES = Object.keys(VALUE_TYPE_LABEL) as ValueType[]
export const AGGREGATIONS = Object.keys(AGGREGATION_LABEL) as Aggregation[]
export const DIRECTIONS = Object.keys(DIRECTION_LABEL) as Direction[]

/** One line describing how a metric is set up: "Count · Add up the day · More is better · reps". */
export function metricSummary(
  metric: Pick<Metric, 'value_type' | 'aggregation' | 'direction' | 'unit'>,
): string {
  const parts = [
    VALUE_TYPE_LABEL[metric.value_type],
    AGGREGATION_LABEL[metric.aggregation],
    DIRECTION_LABEL[metric.direction],
  ]
  if (metric.unit !== null && metric.unit.trim() !== '') parts.push(metric.unit)
  return parts.join(' · ')
}

/**
 * Metrics you manage in Settings: the ones you set up, and the ones a habit made for itself.
 * App metrics (written by screen time) and the journal's metric are Atlas's own.
 */
export function isManagedMetric(metric: Pick<Metric, 'origin'>): boolean {
  return metric.origin === 'manual' || metric.origin === 'habit'
}
