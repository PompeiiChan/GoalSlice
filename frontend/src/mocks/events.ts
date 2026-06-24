import type { ApiResponse } from '@/types/api'
import type { GrowthAsset } from '@/types/asset'
import type {
  ApplyDowngradeResponse,
  CompleteEventResponse,
  DailyEvent,
  DowngradeOptionsResponse,
  TodayEventResponse,
} from '@/types/event'
import { DAY_FEEDBACK, DOWNGRADE_OPTIONS } from './data'
import {
  countCompletedDays,
  currentSessionId,
  loadMockState,
  newId,
  nowIso,
  saveMockState,
} from './storage'

function fail<T>(code: number, message: string): ApiResponse<T> {
  return { code, message, data: null as T }
}

function getTodayEvent(state = loadMockState()): DailyEvent | null {
  if (!state.quest) return null
  return (
    state.events.find(
      (e) => e.day_index === state.quest!.current_day && e.status === 'in_progress',
    ) ??
    state.events.find((e) => e.day_index === state.quest!.current_day) ??
    null
  )
}

export function mockGetTodayEvent(): ApiResponse<TodayEventResponse> {
  const state = loadMockState()
  const event = getTodayEvent(state)
  if (!event || !state.quest) {
    return fail(404, '没有进行中的副本或今日任务')
  }
  return {
    code: 200,
    message: 'success',
    data: {
      event,
      quest_summary: {
        quest_title: state.quest.quest_title,
        current_day: state.quest.current_day,
        total_days: state.quest.total_days,
      },
    },
  }
}

export function mockCompleteEvent(
  eventId: string,
  userOutput?: string,
): ApiResponse<CompleteEventResponse> {
  const state = loadMockState()
  const eventIndex = state.events.findIndex((e) => e.event_id === eventId)
  if (eventIndex < 0 || !state.quest) {
    return fail(404, '任务不存在')
  }

  const event = state.events[eventIndex]
  const now = nowIso()
  const completedEvent: DailyEvent = {
    ...event,
    user_output: userOutput ?? event.user_output,
    status: 'completed',
    completed_at: now,
  }
  state.events[eventIndex] = completedEvent

  const dayIndex = event.day_index
  const feedbackMeta = DAY_FEEDBACK[dayIndex] ?? DAY_FEEDBACK[3]
  const assetId = newId()
  const sessionId = currentSessionId()

  const asset: GrowthAsset = {
    asset_id: assetId,
    session_id: sessionId,
    quest_id: state.quest.quest_id,
    event_id: eventId,
    asset_type: feedbackMeta.asset_type,
    asset_name: feedbackMeta.asset_name,
    asset_content: null,
    created_at: now,
  }
  state.assets.push(asset)

  const completedDays = countCompletedDays(state.events)
  const isQuestCompleted = dayIndex >= 7
  const nextDay = dayIndex + 1
  const nextEvent = state.events.find((e) => e.day_index === nextDay)

  state.quest = { ...state.quest, updated_at: now }

  saveMockState(state)

  return {
    code: 200,
    message: 'success',
    data: {
      event: completedEvent,
      feedback: {
        completion_title: `Day ${dayIndex} 已完成`,
        action_label: feedbackMeta.action_label,
        meaning_text: feedbackMeta.meaning_text,
        asset: {
          asset_id: assetId,
          asset_type: feedbackMeta.asset_type,
          asset_name: feedbackMeta.asset_name,
        },
        progress: { completed_days: completedDays, total_days: 7 },
        tomorrow_preview: nextEvent
          ? { day_index: nextDay, event_title: nextEvent.event_title }
          : { day_index: 7, event_title: '周复盘' },
        is_quest_completed: isQuestCompleted,
      },
    },
  }
}

export function mockDowngradeOptions(eventId: string): ApiResponse<DowngradeOptionsResponse> {
  void eventId
  return {
    code: 200,
    message: 'success',
    data: {
      options: DOWNGRADE_OPTIONS.map(({ option_id, title, description, estimated_time }) => ({
        option_id,
        title,
        description,
        estimated_time,
      })),
    },
  }
}

export function mockApplyDowngrade(
  eventId: string,
  optionId: string,
): ApiResponse<ApplyDowngradeResponse> {
  const state = loadMockState()
  const eventIndex = state.events.findIndex((e) => e.event_id === eventId)
  if (eventIndex < 0) {
    return fail(404, '任务不存在')
  }

  const option = DOWNGRADE_OPTIONS.find((o) => o.option_id === optionId)
  if (!option) {
    return fail(400, '无效的降级方案')
  }

  if (optionId === 'tomorrow') {
    return {
      code: 200,
      message: 'success',
      data: { event: state.events[eventIndex] },
    }
  }

  const original = state.events[eventIndex]
  const newEvent: DailyEvent = {
    event_id: newId(),
    quest_id: original.quest_id,
    day_index: original.day_index,
    event_title: option.event_title,
    event_description: option.event_description,
    estimated_time: option.estimated_time,
    meaning: option.meaning,
    output_type: option.output_type,
    user_output: null,
    status: 'in_progress',
    original_event_id: original.event_id,
    completed_at: null,
  }

  state.events[eventIndex] = { ...original, status: 'downgraded' }
  state.events.push(newEvent)
  saveMockState(state)

  return { code: 200, message: 'success', data: { event: newEvent } }
}

/** 完成反馈页确认后推进至下一天 — Mock 本地状态 */
export function mockAdvanceDayAfterFeedback(): void {
  const state = loadMockState()
  if (!state.quest) return
  const nextDay = state.quest.current_day + 1
  if (nextDay > 7) return
  const nextEvent = state.events.find((e) => e.day_index === nextDay)
  if (nextEvent) {
    const idx = state.events.findIndex((e) => e.event_id === nextEvent.event_id)
    state.events[idx] = { ...nextEvent, status: 'in_progress' }
  }
  state.quest = { ...state.quest, current_day: nextDay, updated_at: nowIso() }
  saveMockState(state)
}
