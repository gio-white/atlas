import type { LabelHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  // Callers associate this primitive with a control via htmlFor or nested inputs.
  return (
    // biome-ignore lint/a11y/noLabelWithoutControl: design-system primitive
    <label className={cn('text-xs font-medium text-muted', className)} {...props} />
  )
}

export { Label }
