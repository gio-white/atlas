import type { ReactElement } from 'react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ROW_ACTION_LABEL, type RowAction } from '@/lib/habits'

/** The row menu for one habit's day (habits brief §7): `children` is the element that opens it. */
export function DayMenu({
  actions,
  onAction,
  open,
  onOpenChange,
  disabled = false,
  children,
}: {
  actions: RowAction[]
  onAction: (action: RowAction) => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
  disabled?: boolean
  children: ReactElement
}) {
  return (
    <DropdownMenu open={open} onOpenChange={onOpenChange}>
      <DropdownMenuTrigger asChild disabled={disabled}>
        {children}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {actions.map((action) => (
          <DropdownMenuItem key={action} onSelect={() => onAction(action)}>
            {ROW_ACTION_LABEL[action]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
