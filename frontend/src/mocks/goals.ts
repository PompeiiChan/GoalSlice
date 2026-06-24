import type { ApiResponse } from '@/types/api'
import type { ActiveGoalResponse, ClarifyGoalResponse, CreateGoalResponse, Goal } from '@/types/goal'
import { buildQuestPreview, CLARIFY_QUESTIONS } from './data'
import {
  currentSessionId,
  hasActiveQuest,
  loadMockState,
  newId,
  nowIso,
  saveMockState,
} from './storage'

const GOAL_TYPE_MAP: Record<string, Goal['goal_type']> = {
  '转行 / 求职': 'career_switch',
  技能提升: 'skill_up',
  面试准备: 'interview_prep',
  作品集建设: 'portfolio',
  个人品牌: 'personal_brand',
  其他: 'other',
}

const TIME_MAP: Record<string, '5m' | '15m' | '30m' | '60m_plus' | 'flexible'> = {
  '5 分钟': '5m',
  '15 分钟': '15m',
  '30 分钟': '30m',
  '60m_plus': '60m_plus',
  '60 分钟以上': '60m_plus',
  '不固定，看当天状态': 'flexible',
}

function fail<T>(code: number, message: string): ApiResponse<T> {
  return { code, message, data: null as T }
}

export function mockCreateGoal(rawGoal: string): ApiResponse<CreateGoalResponse> {
  if (!rawGoal?.trim()) {
    return fail(400, 'raw_goal 不能为空')
  }
  const state = loadMockState()
  if (hasActiveQuest(state)) {
    return fail(422, '已有进行中的副本，请先完成或暂停')
  }

  const sessionId = currentSessionId()
  const now = nowIso()
  const goal: Goal = {
    goal_id: newId(),
    session_id: sessionId,
    raw_goal: rawGoal.trim(),
    goal_type: rawGoal.includes('会议总结') ? 'skill_up' : null,
    refined_goal: null,
    weekly_outcome: null,
    status: 'active',
    created_at: now,
    updated_at: now,
  }

  state.goal = goal
  state.context = null
  state.preview = null
  state.quest = null
  state.events = []
  state.assets = []
  state.reviewGenerated = false
  state.review = null
  saveMockState(state)

  return {
    code: 200,
    message: 'success',
    data: {
      goal,
      clarify_questions: CLARIFY_QUESTIONS,
    },
  }
}

export function mockClarifyGoal(
  goalId: string,
  answers: Record<string, string>,
  notes = '',
): ApiResponse<ClarifyGoalResponse> {
  const state = loadMockState()
  if (!state.goal || state.goal.goal_id !== goalId) {
    return fail(404, '目标不存在')
  }

  const sessionId = currentSessionId()
  const goalTypeLabel = answers.goal_type ?? '技能提升'
  const goalType = GOAL_TYPE_MAP[goalTypeLabel] ?? 'skill_up'
  const weeklyOutcome = answers.weekly_outcome ?? '完成一个具体产物'
  const now = nowIso()

  const goal: Goal = {
    ...state.goal,
    goal_type: goalType,
    refined_goal: state.goal.raw_goal.includes('会议总结')
      ? '提升会议总结能力'
      : state.goal.raw_goal.replace(/^我想/, '').trim(),
    weekly_outcome: weeklyOutcome,
    updated_at: now,
  }

  const context = {
    session_id: sessionId,
    goal_type: goalType,
    weekly_outcome: weeklyOutcome,
    available_time: TIME_MAP[answers.available_time ?? '15 分钟'] ?? '15m',
    current_level: answers.current_level ?? '有一点了解，但不系统',
    failure_reason: answers.failure_reason ?? '不知道第一步做什么',
    preferred_intensity: 'low',
    notes: notes ?? '',
  }

  state.goal = goal
  state.context = context
  state.preview = buildQuestPreview()
  saveMockState(state)

  return {
    code: 200,
    message: 'success',
    data: { goal, context },
  }
}

export function mockGetActiveGoal(): ApiResponse<ActiveGoalResponse> {
  const state = loadMockState()
  if (!state.goal) {
    return fail(404, '目标不存在')
  }

  const savedAnswers: Record<string, string> = {}
  if (state.context) {
    const reverseGoalType = Object.entries(GOAL_TYPE_MAP).find(
      ([, code]) => code === state.context?.goal_type,
    )?.[0]
    if (reverseGoalType) savedAnswers.goal_type = reverseGoalType
    if (state.context.weekly_outcome) savedAnswers.weekly_outcome = state.context.weekly_outcome
  }

  return {
    code: 200,
    message: 'success',
    data: {
      goal: state.goal,
      clarify_questions: CLARIFY_QUESTIONS,
      saved_answers: savedAnswers,
      context: state.context,
    },
  }
}
