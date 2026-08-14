import type { InputHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'h-9 w-full rounded-lg border border-line bg-canvas px-3 text-sm text-ink placeholder:text-muted motion-safe:transition-shadow motion-safe:duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        className,
      )}
      {...props}
    />
  )
}

export { Input }
