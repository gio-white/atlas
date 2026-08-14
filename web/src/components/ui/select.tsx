import type { SelectHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        'h-9 w-full cursor-pointer rounded-lg border border-line bg-canvas px-3 text-sm text-ink motion-safe:transition-shadow motion-safe:duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        className,
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export { Select }
