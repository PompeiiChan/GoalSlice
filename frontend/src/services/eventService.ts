import type { ApiResponse } from '@/types/api'
import type {
  ApplyDowngradeResponse,
  CompleteEventResponse,
  DowngradeOptionsResponse,
  TodayEventResponse,
} from '@/types/event'
import {
  mockAdvanceDayAfterFeedback,
  mockApplyDowngrade,
  mockCompleteEvent,
  mockDowngradeOptions,
  mockGetTodayEvent,
} from '@/mocks'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

function assertOk<T>(res: ApiResponse<T>): T {
  if (res.code !== 200 || res.data === null) {
    throw new Error(res.message || '请求失败')
  }
  return res.data
}

export const eventService = {
  async getToday(): Promise<TodayEventResponse> {
    if (useMock) {
      return assertOk(mockGetTodayEvent())
    }
    const { default: api } = await import('./api')
    const { data } = await api.get<ApiResponse<TodayEventResponse>>('/v1/events/today')
    return assertOk(data)
  },

  async complete(eventId: string, userOutput?: string): Promise<CompleteEventResponse> {
    if (useMock) {
      return assertOk(mockCompleteEvent(eventId, userOutput))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<CompleteEventResponse>>(
      `/v1/events/${eventId}/complete`,
      { user_output: userOutput },
    )
    return assertOk(data)
  },

  async getDowngradeOptions(eventId: string): Promise<DowngradeOptionsResponse> {
    if (useMock) {
      return assertOk(mockDowngradeOptions(eventId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.post<ApiResponse<DowngradeOptionsResponse>>(
      `/v1/events/${eventId}/downgrade`,
      { reason: '今天太难了' },
    )
    return assertOk(data)
  },

  async applyDowngrade(eventId: string, optionId: string): Promise<ApplyDowngradeResponse> {
    if (useMock) {
      return assertOk(mockApplyDowngrade(eventId, optionId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.patch<ApiResponse<ApplyDowngradeResponse>>(
      `/v1/events/${eventId}/apply-downgrade`,
      { option_id: optionId },
    )
    return assertOk(data)
  },

  advanceDayAfterFeedback(): void {
    if (useMock) {
      mockAdvanceDayAfterFeedback()
    }
  },
}
