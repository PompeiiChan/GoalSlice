import type { GrowthAsset } from '@/types/asset'
import type { DailyEvent } from '@/types/event'
import type { Goal, UserContext } from '@/types/goal'
import type { Quest, QuestPreview } from '@/types/quest'
import { getStoredSessionId } from '@/utils/session'

import type { ReviewData } from '@/types/quest'

const MOCK_STATE_KEY = 'goalslice_mock_state'

export interface MockState {
  goal: Goal | null
  context: UserContext | null
  preview: QuestPreview | null
  quest: Quest | null
  events: DailyEvent[]
  assets: GrowthAsset[]
  reviewGenerated: boolean
  review: ReviewData | null
}

function emptyState(): MockState {
  return {
    goal: null,
    context: null,
    preview: null,
    quest: null,
    events: [],
    assets: [],
    reviewGenerated: false,
    review: null,
  }
}

export function loadMockState(): MockState {
  try {
    const raw = localStorage.getItem(MOCK_STATE_KEY)
    if (!raw) return emptyState()
    return { ...emptyState(), ...JSON.parse(raw) } as MockState
  } catch {
    return emptyState()
  }
}

export function saveMockState(state: MockState): void {
  localStorage.setItem(MOCK_STATE_KEY, JSON.stringify(state))
}

export function clearMockState(): void {
  localStorage.removeItem(MOCK_STATE_KEY)
}

export function currentSessionId(): string {
  return getStoredSessionId() ?? 'mock-session'
}

export function newId(): string {
  return crypto.randomUUID()
}

export function nowIso(): string {
  return new Date().toISOString()
}

export function hasActiveQuest(state: MockState = loadMockState()): boolean {
  return state.quest?.status === 'in_progress'
}

export function countCompletedDays(events: DailyEvent[]): number {
  return events.filter((e) => e.status === 'completed').length
}
