import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize',
  {
    variants: {
      tone: {
        default: 'bg-raised text-muted',
        good: 'bg-good/12 text-good',
        warn: 'bg-warn/15 text-warn',
        bad: 'bg-bad/12 text-bad',
        accent: 'bg-accent/12 text-accent',
      },
    },
    defaultVariants: {
      tone: 'default',
    },
  },
)

type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>

function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />
}

export { Badge, badgeVariants }
