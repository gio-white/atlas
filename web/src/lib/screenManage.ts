import type { Period, ScreenBudget } from './api'
import { formatComparator, formatMinutes } from './format'

const PERIOD_PHRASE: Record<Period, string> = { day: 'a day', week: 'a week', month: 'a month' }

export function budgetSlug(targetSlug: string, period: Period): string {
  return `${targetSlug}-${period}-cap`
}

export function budgetSummary(
  budget: Pick<ScreenBudget, 'comparator' | 'target_value' | 'period'>,
) {
  return `${formatComparator(budget.comparator)} ${formatMinutes(budget.target_value)} ${PERIOD_PHRASE[budget.period]}`
}

export type BudgetState = { label: string; open: boolean; counting: boolean }

/**
 * `active_to` is inclusive, so a cap ended today still counts today ("last day"). `open` is
 * whether it has no end date yet, which decides between End and Resume.
 */
export function budgetState(
  budget: Pick<ScreenBudget, 'active_from' | 'active_to'>,
  asOf: string,
): BudgetState {
  if (budget.active_from > asOf) {
    return {
      label: `starts ${budget.active_from}`,
      open: budget.active_to === null,
      counting: false,
    }
  }
  if (budget.active_to === null) return { label: 'active', open: true, counting: true }
  if (budget.active_to < asOf)
    return { label: `ended ${budget.active_to}`, open: false, counting: false }
  return { label: `last day ${budget.active_to}`, open: false, counting: true }
}
