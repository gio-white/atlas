import { type FormEvent, useEffect, useMemo, useState } from 'react'

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
import { ApiError, createTask, type Goal, type TaskBucket, type TaskPriority } from '@/lib/api'
import { HORIZON_META } from '@/lib/horizons'
import { activeGoals, TASK_BUCKET_META, TASK_BUCKETS } from '@/lib/tasks'

const PRIORITIES: TaskPriority[] = ['high', 'normal', 'low']

export function TaskCreateDialog({
  open,
  onOpenChange,
  goals,
  onCreated,
  defaultGoal = null,
  defaultBucket = 'today',
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  goals: Goal[]
  onCreated: () => Promise<void>
  defaultGoal?: string | null
  defaultBucket?: TaskBucket
}) {
  const choices = useMemo(() => activeGoals(goals), [goals])
  const [title, setTitle] = useState('')
  const [bucket, setBucket] = useState<TaskBucket>(defaultBucket)
  const [priority, setPriority] = useState<TaskPriority>('normal')
  const [dueOn, setDueOn] = useState('')
  const [goal, setGoal] = useState(defaultGoal ?? '')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!open) return
    setTitle('')
    setBucket(defaultBucket)
    setPriority('normal')
    setDueOn('')
    setGoal(defaultGoal ?? '')
    setError(null)
    setPending(false)
  }, [open, defaultBucket, defaultGoal])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const cleaned = title.trim()
    if (cleaned === '') {
      setError('title must be a non-empty string')
      return
    }
    setError(null)
    setPending(true)
    try {
      await createTask({
        title: cleaned,
        bucket,
        priority,
        due_on: dueOn === '' ? null : dueOn,
        goal: goal === '' ? null : goal,
      })
      onOpenChange(false)
      await onCreated()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not create task')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New task</DialogTitle>
          <DialogDescription>
            Operative work for the day. Completing a task does not log a habit or change goal
            progress.
          </DialogDescription>
        </DialogHeader>
        <form className="grid gap-3" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="task-title">Title</Label>
            <Input
              id="task-title"
              value={title}
              required
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <Label htmlFor="task-bucket">Bucket</Label>
              <Select
                id="task-bucket"
                value={bucket}
                onChange={(event) => setBucket(event.target.value as TaskBucket)}
              >
                {TASK_BUCKETS.map((item) => (
                  <option key={item} value={item}>
                    {TASK_BUCKET_META[item].label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="task-priority">Priority</Label>
              <Select
                id="task-priority"
                value={priority}
                onChange={(event) => setPriority(event.target.value as TaskPriority)}
              >
                {PRIORITIES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <Label htmlFor="task-due">Due (optional)</Label>
              <Input
                id="task-due"
                type="date"
                value={dueOn}
                onChange={(event) => setDueOn(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="task-goal">Goal (optional)</Label>
              <Select id="task-goal" value={goal} onChange={(event) => setGoal(event.target.value)}>
                <option value="">No goal</option>
                {choices.map((item) => (
                  <option key={item.slug} value={item.slug}>
                    {item.name} · {HORIZON_META[item.horizon].label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" disabled={pending || title.trim() === ''}>
            Create task
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
