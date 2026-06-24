import type { ApiResponse } from '@/types/api'
import type {
  AcceptQuestResponse,
  ActiveQuestResponse,
  NextWeekResponse,
  PauseQuestResponse,
  QuestDetailResponse,
  QuestPreview,
  ReviewResponse,
} from '@/types/quest'
import {
  mockAcceptQuest,
  mockGenerateQuest,
  mockGetActiveQuest,
  mockGetQuestDetail,
  mockNextWeek,
  mockPauseQuest,
  mockReviewQuest,
} from '@/mocks'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

function assertOk<T>(res: ApiResponse<T>): T {
  if (res.code !== 200) {
    throw new Error(res.message || '请求失败')
  }
  return res.data as T
}

export const questService = {
  async generatePreview(goalId: string): Promise<{ preview: QuestPreview }> {
    if (useMock) {
      return assertOk(mockGenerateQuest(goalId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<{ preview: QuestPreview }>>('/v1/quests/generate', {
      goal_id: goalId,
    })
    return assertOk(data)
  },

  async acceptQuest(goalId: string, preview?: QuestPreview): Promise<AcceptQuestResponse> {
    if (useMock) {
      return assertOk(mockAcceptQuest(goalId))
    }
    const { default: api } = await import('./api')
    const body: {
      goal_id: string
      preview?: { quest_title: string; success_condition: string; days: QuestPreview['days'] }
    } = { goal_id: goalId }
    if (preview) {
      body.preview = {
        quest_title: preview.quest_title,
        success_condition: preview.success_condition,
        days: preview.days,
      }
    }
    const { data } = await api.post<ApiResponse<AcceptQuestResponse>>('/v1/quests', body)
    return assertOk(data)
  },

  async getActive(): Promise<ActiveQuestResponse | null> {
    if (useMock) {
      return assertOk(mockGetActiveQuest())
    }
    const { default: api } = await import('./api')
    const { data } = await api.get<ApiResponse<ActiveQuestResponse | null>>('/v1/quests/active')
    return assertOk(data)
  },

  async getDetail(questId: string): Promise<QuestDetailResponse> {
    if (useMock) {
      return assertOk(mockGetQuestDetail(questId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.get<ApiResponse<QuestDetailResponse>>(`/v1/quests/${questId}`)
    return assertOk(data)
  },

  async review(questId: string): Promise<ReviewResponse> {
    if (useMock) {
      return assertOk(mockReviewQuest(questId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<ReviewResponse>>(`/v1/quests/${questId}/review`)
    return assertOk(data)
  },

  async nextWeek(questId: string): Promise<NextWeekResponse> {
    if (useMock) {
      return assertOk(mockNextWeek(questId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<NextWeekResponse>>(`/v1/quests/${questId}/next-week`, {
      accept_suggestion: true,
    })
    return assertOk(data)
  },

  async pause(questId: string): Promise<PauseQuestResponse> {
    if (useMock) {
      return assertOk(mockPauseQuest(questId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<PauseQuestResponse>>(`/v1/quests/${questId}/pause`)
    return assertOk(data)
  },
}
