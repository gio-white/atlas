import { cn } from '@/lib/utils'

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: { id: T; label: string }[]
  value: T
  onChange: (next: T) => void
  label: string
}) {
  return (
    <div className="inline-flex gap-1 rounded-lg bg-raised p-1" role="tablist" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          role="tab"
          aria-selected={value === option.id}
          className={cn(
            'min-h-8 rounded-md px-3 text-xs font-medium',
            value === option.id ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
          )}
          onClick={() => onChange(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
