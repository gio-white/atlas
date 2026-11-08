// Builders for quest read models in component tests. Values mirror what the API sends.
import type { Chapter, QuestMilestone, QuestTask, SideQuest } from '@/lib/api'

const STAMP = '2026-11-01T09:00:00Z'

export function task(id: number, title: string, overrides: Partial<QuestTask> = {}): QuestTask {
  return {
    id,
    title,
    description: null,
    status: 'todo',
    priority: 'normal',
    estimate_minutes: null,
    due_on: null,
    weight: null,
    weight_share: null,
    position: id,
    parent: null,
    path: [],
    inbox: false,
    standalone: false,
    organized_at: STAMP,
    started_at: null,
    completed_at: null,
    archived_at: null,
    created_at: STAMP,
    updated_at: STAMP,
    planned_minutes: 0,
    block_count: 0,
    ...overrides,
  }
}

const STATE = {
  position: 0,
  archived_at: null,
  created_at: STAMP,
  updated_at: STAMP,
  path: [],
  description: null,
  planned_minutes: 0,
  eligible: false,
  open_children: [],
  next_action: null,
}

export function chapter(id: number, title: string, overrides: Partial<Chapter> = {}): Chapter {
  return {
    ...STATE,
    id,
    title,
    milestone_id: 1,
    side_quest_id: null,
    weight: null,
    weight_share: 0.5,
    state: 'not_started',
    task_count: 0,
    progress: 0,
    done_tasks: 0,
    total_tasks: 0,
    ...overrides,
  }
}

export function milestone(
  id: number,
  title: string,
  overrides: Partial<QuestMilestone> = {},
): QuestMilestone {
  return {
    ...STATE,
    id,
    title,
    goal_id: 1,
    due_on: null,
    weight: null,
    weight_share: 1,
    chapter_count: 0,
    task_count: 0,
    progress: 0,
    done_tasks: 0,
    total_tasks: 0,
    status: 'active',
    completed_at: null,
    completed_with_open_items: false,
    ...overrides,
  }
}

export function sideQuest(
  id: number,
  title: string,
  overrides: Partial<SideQuest> = {},
): SideQuest {
  return {
    ...STATE,
    id,
    title,
    due_on: null,
    chapter_count: 0,
    task_count: 0,
    progress: null,
    done_tasks: 0,
    total_tasks: 0,
    status: 'active',
    completed_at: null,
    completed_with_open_items: false,
    ...overrides,
  }
}
