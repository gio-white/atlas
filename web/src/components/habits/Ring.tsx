import { cn } from '@/lib/utils'

/** A small ring filled clockwise to `share` (0–1) in the accent colour, on a quiet track. */
export function Ring({
  share,
  size = 20,
  className,
}: {
  share: number
  size?: number
  className?: string
}) {
  const stroke = size >= 20 ? 3 : 2.5
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const filled = Math.min(1, Math.max(0, share)) * circumference
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={cn('-rotate-90', className)}
      aria-hidden="true"
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        strokeWidth={stroke}
        className="stroke-line"
      />
      {filled > 0 && (
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          className="stroke-accent"
        />
      )}
    </svg>
  )
}
