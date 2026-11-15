import { Flame } from 'lucide-react'

/** The streak: a small accent flame, then "12 days" (habits brief §12–13). */
export function Streak({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      <Flame className="size-3.5 text-accent" aria-hidden />
      {label}
    </span>
  )
}
