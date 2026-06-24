import type { ApiResponse } from '@/types/api'
import type { DailyEvent } from '@/types/event'
import type {
  AcceptQuestResponse,
  ActiveQuestResponse,
  NextWeekResponse,
  PauseQuestResponse,
  Quest,
  QuestDetailResponse,
  QuestPreview,
  ReviewResponse,
} from '@/types/quest'
import {
  buildQuestPreview,
  DAILY_EVENT_TITLE_OVERRIDE,
  NEXT_WEEK_SUGGESTION,
  REVIEW_BOSS_SUMMARY,
  REVIEW_OBSERVATION,
  REVIEW_OUTPUTS,
} from './data'
import {
  countCompletedDays,
  loadMockState,
  newId,
  nowIso,
  saveMockState,
} from './storage'

function fail<T>(code: number, message: string): ApiResponse<T> {
  return { code, message, data: null as T }
}

export function mockGenerateQuest(goalId: string): ApiResponse<{ preview: QuestPreview }> {
  const state = loadMockState()
  if (!state.goal || state.goal.goal_id !== goalId) {
    return fail(404, '目标不存在')
  }
  const preview = state.preview ?? buildQuestPreview()
  state.preview = preview
  saveMockState(state)
  return { code: 200, message: 'success', data: { preview } }
}

export function mockAcceptQuest(goalId: string): ApiResponse<AcceptQuestResponse> {
  const state = loadMockState()
  if (!state.goal || state.goal.goal_id !== goalId) {
    return fail(404, '目标不存在')
  }
  const preview = state.preview ?? buildQuestPreview()
  const now = nowIso()
  const questId = newId()

  const quest: Quest = {
    quest_id: questId,
    goal_id: goalId,
    quest_title: preview.quest_title,
    success_condition: preview.success_condition,
    total_days: 7,
    current_day: 1,
    status: 'in_progress',
    created_at: now,
    updated_at: now,
  }

  const events: DailyEvent[] = preview.days.map((day) => ({
    event_id: newId(),
    quest_id: questId,
    day_index: day.day_index,
    event_title: DAILY_EVENT_TITLE_OVERRIDE[day.day_index] ?? day.event_title,
    event_description: day.event_description,
    estimated_time: day.estimated_time,
    meaning: day.meaning,
    output_type: day.output_type,
    user_output: null,
    status: day.day_index === 1 ? 'in_progress' : 'pending',
    original_event_id: null,
    completed_at: null,
  }))

  const todayEvent = events.find((e) => e.day_index === 1)!
  state.quest = quest
  state.events = events
  saveMockState(state)

  return {
    code: 200,
    message: 'success',
    data: { quest, today_event: todayEvent },
  }
}

export function mockGetActiveQuest(): ApiResponse<ActiveQuestResponse | null> {
  const state = loadMockState()
  if (!state.quest || state.quest.status !== 'in_progress') {
    return { code: 200, message: 'success', data: null }
  }
  const completed = countCompletedDays(state.events)
  return {
    code: 200,
    message: 'success',
    data: {
      quest: state.quest,
      progress: { completed_days: completed, total_days: state.quest.total_days },
      assets_count: state.assets.length,
    },
  }
}

export function mockGetQuestDetail(questId: string): ApiResponse<QuestDetailResponse> {
  const state = loadMockState()
  if (!state.quest || state.quest.quest_id !== questId) {
    return fail(404, '副本不存在')
  }

  const days = state.events
    .slice()
    .sort((a, b) => a.day_index - b.day_index)
    .map((e) => {
      const previewDay = state.preview?.days.find((d) => d.day_index === e.day_index)
      return {
        day_index: e.day_index,
        event_title: e.event_title,
        estimated_time: e.estimated_time,
        status: e.status === 'completed' ? 'completed' : 'pending',
        is_boss: previewDay?.is_boss ?? e.day_index === 7,
      }
    })

  return {
    code: 200,
    message: 'success',
    data: { quest: state.quest, days },
  }
}

export function mockReviewQuest(questId: string): ApiResponse<ReviewResponse> {
  const stored = mockGetStoredReview(questId)
  if (stored) return stored

  const state = loadMockState()
  if (!state.quest || state.quest.quest_id !== questId) {
    return fail(404, '副本不存在')
  }

  const completed = countCompletedDays(state.events)
  const quest: Quest = { ...state.quest, status: 'completed', current_day: 7 }
  state.quest = quest
  state.reviewGenerated = true
  const reviewData = {
    completed_count: completed,
    total_days: 7,
    outputs: REVIEW_OUTPUTS,
    assets: state.assets.map((a) => ({
      asset_id: a.asset_id,
      asset_type: a.asset_type,
      asset_name: a.asset_name,
    })),
    observations: [REVIEW_OBSERVATION],
    boss_summary: REVIEW_BOSS_SUMMARY,
    next_week_suggestion: NEXT_WEEK_SUGGESTION,
  }
  state.review = reviewData
  saveMockState(state)

  return {
    code: 200,
    message: 'success',
    data: {
      review: reviewData,
      quest: { quest_id: quest.quest_id, status: quest.status, current_day: quest.current_day },
    },
  }
}

export function mockGetStoredReview(questId: string): ApiResponse<ReviewResponse> | null {
  const state = loadMockState()
  if (!state.review || !state.quest || state.quest.quest_id !== questId) return null
  return {
    code: 200,
    message: 'success',
    data: {
      review: state.review,
      quest: { quest_id: state.quest.quest_id, status: state.quest.status, current_day: state.quest.current_day },
    },
  }
}

export function mockNextWeek(questId: string): ApiResponse<NextWeekResponse> {
  const state = loadMockState()
  if (!state.quest || state.quest.quest_id !== questId) {
    return fail(404, '副本不存在')
  }
  const goalId = state.goal?.goal_id ?? newId()
  state.quest = null
  state.events = []
  state.preview = null
  state.reviewGenerated = false
  state.review = null
  if (state.goal) {
    state.goal = { ...state.goal, status: 'active', updated_at: nowIso() }
  }
  saveMockState(state)
  return {
    code: 200,
    message: 'success',
    data: { goal_id: goalId, redirect: 'clarify', message: '已准备好进入下一周副本' },
  }
}

export function mockPauseQuest(questId: string): ApiResponse<PauseQuestResponse> {
  const state = loadMockState()
  if (!state.quest || state.quest.quest_id !== questId) {
    return fail(404, '副本不存在')
  }
  state.quest = { ...state.quest, status: 'abandoned', updated_at: nowIso() }
  if (state.goal) {
    state.goal = { ...state.goal, status: 'paused', updated_at: nowIso() }
  }
  saveMockState(state)
  return {
    code: 200,
    message: 'success',
    data: { quest_id: questId, status: 'abandoned' },
  }
}
