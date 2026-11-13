import { CircleCheck, PenLine, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

/** The header's Add button: a task for the Inbox, or an entry for a metric. */
export function AddMenu({ onTask, onEntry }: { onTask: () => void; onEntry: () => void }) {
  return (
    // Not modal: its items open dialogs, and a modal menu closing under a dialog leaves the
    // page unclickable once that dialog closes.
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button type="button" className="bg-iris hover:bg-iris/90 focus-visible:ring-iris">
          <Plus className="size-4" aria-hidden />
          Add
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={onTask}>
          <CircleCheck className="size-4 text-muted" aria-hidden />
          Task
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onEntry}>
          <PenLine className="size-4 text-muted" aria-hidden />
          Entry
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
