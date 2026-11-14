import { Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { notifyHabitsChanged } from '@/lib/habits'

import { HabitSheet } from './HabitSheet'

/** "New habit": opens the habit sheet; a created habit shows on the Day and Week tabs at once. */
export function NewHabitButton({ size = 'default' }: { size?: 'default' | 'sm' }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button type="button" size={size} onClick={() => setOpen(true)}>
        <Plus className="size-4" aria-hidden />
        New habit
      </Button>
      <HabitSheet open={open} onOpenChange={setOpen} onSaved={notifyHabitsChanged} />
    </>
  )
}
