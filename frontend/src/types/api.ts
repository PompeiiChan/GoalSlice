/** 统一 API 响应包装 — 对齐 docs/api-contracts.md */

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export type GoalType =
  | 'career_switch'
  | 'skill_up'
  | 'interview_prep'
  | 'portfolio'
  | 'expression'
  | 'promotion'
  | 'personal_brand'
  | 'other'

export type GoalStatus = 'active' | 'completed' | 'paused'
export type QuestStatus = 'in_progress' | 'completed' | 'abandoned'
export type EventStatus = 'pending' | 'in_progress' | 'completed' | 'downgraded'
export type OutputType = 'text' | 'checkbox'
export type AssetType =
  | 'ability_fragment'
  | 'work_draft'
  | 'interview_story'
  | 'case_note'
  | 'template_fragment'
  | 'other'

export type AvailableTime = '5m' | '15m' | '30m' | '60m_plus' | 'flexible'
