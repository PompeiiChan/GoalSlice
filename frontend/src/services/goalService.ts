import type { ApiResponse } from '@/types/api'
import type {
  ActiveGoalResponse,
  ClarifyGoalResponse,
  CreateGoalResponse,
} from '@/types/goal'
import { mockClarifyGoal, mockCreateGoal, mockGetActiveGoal } from '@/mocks'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

function assertOk<T>(res: ApiResponse<T>): T {
  if (res.code !== 200 || res.data === null) {
    throw new Error(res.message || '请求失败')
  }
  return res.data
}

export const goalService = {
  async createGoal(rawGoal: string): Promise<CreateGoalResponse> {
    if (useMock) {
      return assertOk(mockCreateGoal(rawGoal))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<CreateGoalResponse>>('/v1/goals', { raw_goal: rawGoal })
    return assertOk(data)
  },

  async clarifyGoal(
    goalId: string,
    answers: Record<string, string>,
    notes?: string,
  ): Promise<ClarifyGoalResponse> {
    if (useMock) {
      return assertOk(mockClarifyGoal(goalId, answers, notes))
    }
    const { default: api } = await import('./api')
    const { data } = await api.patch<ApiResponse<ClarifyGoalResponse>>(`/v1/goals/${goalId}/clarify`, {
      answers,
      notes,
    })
    return assertOk(data)
  },

  async getActiveGoal(): Promise<ActiveGoalResponse | null> {
    if (useMock) {
      return assertOk(mockGetActiveGoal())
    }
    const { default: api } = await import('./api')
    try {
      const { data } = await api.get<ApiResponse<ActiveGoalResponse>>('/v1/goals/active')
      return assertOk(data)
    } catch (err) {
      if (err instanceof Error && err.message.includes('目标不存在')) {
        return null
      }
      throw err
    }
  },
}
