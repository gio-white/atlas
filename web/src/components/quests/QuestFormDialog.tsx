import { Archive, ArchiveRestore } from 'lucide-react'
import { type FormEvent, useEffect, useId, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  type Ambition,
  createAmbition,
  createChapter,
  createMilestone,
  createQuestGoal,
  createSideQuest,
  listAmbitions,
  updateAmbition,
  updateChapter,
  updateMilestone,
  updateQuestGoal,
  updateSideQuest,
} from '@/lib/api'
import { KIND_LABELS, shareLabel } from '@/lib/quests'

import { errorMessage } from './useQuestView'

export type ContainerKind = 'ambition' | 'goal' | 'milestone' | 'side_quest' | 'chapter'

/** The stored fields the form reads when editing; computed fields are ignored. */
export type EditableContainer = {
  id: number
  title: string
  description: string | null
  archived_at: string | null
  target_on?: string | null
  due_on?: string | null
  success_description?: string | null
  ambition_id?: number | null
  weight?: number | null
  weight_share?: number | null
}

export type FormParent =
  | { kind: 'ambition'; id: number | null }
  | { kind: 'goal'; id: number }
  | { kind: 'milestone'; id: number }
  | { kind: 'side_quest'; id: number }

type Fields = {
  title: string
  description: string
  date: string
  success: string
  ambition: string
  weight: string
}

const DATE_LABEL: Partial<Record<ContainerKind, string>> = {
  ambition: 'Target date (optional)',
  goal: 'Due date (optional)',
  milestone: 'Due date (optional)',
  side_quest: 'Due date (optional)',
}

const HAS_WEIGHT: Record<ContainerKind, boolean> = {
  ambition: false,
  goal: true,
  milestone: true,
  side_quest: false,
  chapter: true,
}

const TITLE_HINT: Record<ContainerKind, string> = {
  ambition: 'A direction, like “Become a better engineer”',
  goal: 'An outcome, like “Move to Copenhagen”',
  milestone: 'An important result on the way',
  side_quest: 'Something on the side, like “Tax declaration”',
  chapter: 'A batch of tasks, about a week of work',
}

type FormProps = {
  onOpenChange: (open: boolean) => void
  kind: ContainerKind
  /** Where a new item goes (create mode). */
  parent?: FormParent
  /** The item to edit; omit to create. */
  item?: EditableContainer
  /** Parent title for the weight hint. */
  parentTitle?: string
  onSaved: (saved: { id: number }) => void
}

/** Create or edit any container. The form mounts fresh each time the dialog opens. */
export function QuestFormDialog({ open, ...props }: FormProps & { open: boolean }) {
  return (
    <Dialog open={open} onOpenChange={props.onOpenChange}>
      <DialogContent>
        <QuestForm {...props} />
      </DialogContent>
    </Dialog>
  )
}

function QuestForm({ onOpenChange, kind, parent, item, parentTitle, onSaved }: FormProps) {
  const formId = useId()
  const [fields, setFields] = useState<Fields>(() => fieldsOf(item, parent))
  const [ambitions, setAmbitions] = useState<Ambition[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const level = KIND_LABELS[kind]
  const editing = item !== undefined

  useEffect(() => {
    if (kind !== 'goal') return
    listAmbitions()
      .then(setAmbitions)
      .catch(() => setAmbitions([]))
  }, [kind])

  async function save(event: FormEvent) {
    event.preventDefault()
    const title = fields.title.trim()
    if (title === '') {
      setError('Give it a title.')
      return
    }
    let weight: number | null = null
    if (HAS_WEIGHT[kind] && fields.weight.trim() !== '') {
      weight = Number(fields.weight)
      if (!Number.isFinite(weight) || weight <= 0) {
        setError('The weight is a number above zero, or leave it empty.')
        return
      }
    }
    const description = fields.description.trim() === '' ? null : fields.description.trim()
    const date = fields.date === '' ? null : fields.date
    setBusy(true)
    setError(null)
    try {
      const saved = await persist(kind, item, parent, {
        title,
        description,
        date,
        weight,
        success: fields.success.trim() === '' ? null : fields.success.trim(),
        ambitionId: fields.ambition === '' ? null : Number(fields.ambition),
      })
      onSaved(saved)
      onOpenChange(false)
    } catch (caught) {
      setError(errorMessage(caught, `Couldn't save the ${level.toLowerCase()}.`))
    } finally {
      setBusy(false)
    }
  }

  async function toggleArchive() {
    if (item === undefined) return
    setBusy(true)
    setError(null)
    try {
      const archived = item.archived_at === null
      const saved = await ARCHIVE[kind](item.id, archived)
      onSaved(saved)
      onOpenChange(false)
    } catch (caught) {
      setError(errorMessage(caught, `Couldn't archive the ${level.toLowerCase()}.`))
    } finally {
      setBusy(false)
    }
  }

  const share = item?.weight_share === undefined ? null : shareLabel(item.weight_share ?? null)

  return (
    <>
      <DialogHeader>
        <DialogTitle>
          {editing ? `Edit ${level.toLowerCase()}` : `New ${level.toLowerCase()}`}
        </DialogTitle>
        <DialogDescription>{TITLE_HINT[kind]}</DialogDescription>
      </DialogHeader>
      <form id={formId} className="flex flex-col gap-4" onSubmit={save}>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${formId}-title`}>Title</Label>
          <Input
            id={`${formId}-title`}
            autoFocus
            value={fields.title}
            onChange={(event) => setFields({ ...fields, title: event.target.value })}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`${formId}-description`}>Description (optional)</Label>
          <textarea
            id={`${formId}-description`}
            rows={2}
            className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            value={fields.description}
            onChange={(event) => setFields({ ...fields, description: event.target.value })}
          />
        </div>
        {kind === 'goal' && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={`${formId}-success`}>What success looks like (optional)</Label>
            <textarea
              id={`${formId}-success`}
              rows={2}
              className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value={fields.success}
              onChange={(event) => setFields({ ...fields, success: event.target.value })}
            />
          </div>
        )}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {kind === 'goal' && (
            <div className="flex flex-col gap-1.5 sm:col-span-2">
              <Label htmlFor={`${formId}-ambition`}>Ambition (optional)</Label>
              <Select
                id={`${formId}-ambition`}
                value={fields.ambition}
                onChange={(event) => setFields({ ...fields, ambition: event.target.value })}
              >
                <option value="">None, an independent goal</option>
                {ambitions.map((ambition) => (
                  <option key={ambition.id} value={String(ambition.id)}>
                    {ambition.title}
                  </option>
                ))}
              </Select>
            </div>
          )}
          {DATE_LABEL[kind] !== undefined && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`${formId}-date`}>{DATE_LABEL[kind]}</Label>
              <Input
                id={`${formId}-date`}
                type="date"
                value={fields.date}
                onChange={(event) => setFields({ ...fields, date: event.target.value })}
              />
            </div>
          )}
          {HAS_WEIGHT[kind] && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`${formId}-weight`}>Weight (optional)</Label>
              <Input
                id={`${formId}-weight`}
                type="number"
                inputMode="decimal"
                min={0}
                step="any"
                placeholder="1"
                value={fields.weight}
                onChange={(event) => setFields({ ...fields, weight: event.target.value })}
              />
            </div>
          )}
        </div>
        {HAS_WEIGHT[kind] && (
          <p className="-mt-2 text-xs text-muted">
            Weights are relative to the items beside it. Empty counts as 1.
            {share !== null &&
              ` It now counts for ${share}${parentTitle ? ` of ${parentTitle}` : ''}.`}
          </p>
        )}
        {error !== null && (
          <p role="alert" className="text-sm text-bad">
            {error}
          </p>
        )}
        <div className="flex flex-wrap items-center justify-end gap-2">
          {editing && (
            <Button
              type="button"
              variant="ghost"
              className="mr-auto"
              disabled={busy}
              onClick={() => void toggleArchive()}
            >
              {item.archived_at === null ? (
                <>
                  <Archive className="size-4" aria-hidden />
                  Archive
                </>
              ) : (
                <>
                  <ArchiveRestore className="size-4" aria-hidden />
                  Restore
                </>
              )}
            </Button>
          )}
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="submit" disabled={busy}>
            {editing ? 'Save changes' : `Create ${level.toLowerCase()}`}
          </Button>
        </div>
      </form>
    </>
  )
}

function fieldsOf(item?: EditableContainer, parent?: FormParent): Fields {
  return {
    title: item?.title ?? '',
    description: item?.description ?? '',
    date: item?.target_on ?? item?.due_on ?? '',
    success: item?.success_description ?? '',
    ambition:
      item?.ambition_id != null
        ? String(item.ambition_id)
        : item === undefined && parent?.kind === 'ambition' && parent.id !== null
          ? String(parent.id)
          : '',
    weight: item?.weight == null ? '' : String(item.weight),
  }
}

type Values = {
  title: string
  description: string | null
  date: string | null
  weight: number | null
  success: string | null
  ambitionId: number | null
}

function persist(
  kind: ContainerKind,
  item: EditableContainer | undefined,
  parent: FormParent | undefined,
  values: Values,
): Promise<{ id: number }> {
  const { title, description, date, weight, success, ambitionId } = values
  if (kind === 'ambition') {
    const body = { title, description, target_on: date }
    return item ? updateAmbition(item.id, body) : createAmbition(body)
  }
  if (kind === 'goal') {
    const body = {
      title,
      description,
      due_on: date,
      weight,
      success_description: success,
      ambition_id: ambitionId,
    }
    return item ? updateQuestGoal(item.id, body) : createQuestGoal(body)
  }
  if (kind === 'side_quest') {
    const body = { title, description, due_on: date }
    return item ? updateSideQuest(item.id, body) : createSideQuest(body)
  }
  if (kind === 'milestone') {
    const body = { title, description, due_on: date, weight }
    if (item) return updateMilestone(item.id, body)
    if (parent?.kind !== 'goal') throw new Error('A milestone needs a goal')
    return createMilestone({ ...body, goal_id: parent.id })
  }
  const body = { title, description, weight }
  if (item) return updateChapter(item.id, body)
  if (parent?.kind === 'milestone') return createChapter({ ...body, milestone_id: parent.id })
  if (parent?.kind === 'side_quest') return createChapter({ ...body, side_quest_id: parent.id })
  throw new Error('A chapter needs a milestone or side quest')
}

const ARCHIVE: Record<ContainerKind, (id: number, archived: boolean) => Promise<{ id: number }>> = {
  ambition: (id, archived) => updateAmbition(id, { archived }),
  goal: (id, archived) => updateQuestGoal(id, { archived }),
  milestone: (id, archived) => updateMilestone(id, { archived }),
  side_quest: (id, archived) => updateSideQuest(id, { archived }),
  chapter: (id, archived) => updateChapter(id, { archived }),
}
