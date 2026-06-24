import type { AssetType, OutputType, QuestStatus } from './api'
import type { Goal } from './goal'

export interface QuestPreviewDay {
  day_index: number
  event_title: string
  event_description: string
  estimated_time: string
  meaning: string
  output_type: OutputType
  is_boss: boolean
}

export interface QuestPreview {
  quest_title: string
  success_condition: string
  total_estimated_time: string
  days: QuestPreviewDay[]
}

export interface Quest {
  quest_id: string
  goal_id: string
  quest_title: string
  success_condition: string
  total_days: number
  current_day: number
  status: QuestStatus
  created_at: string
  updated_at: string
}

export interface QuestDaySummary {
  day_index: number
  event_title: string
  estimated_time: string
  status: string
  is_boss: boolean
}

export interface ActiveQuestResponse {
  quest: Quest
  progress: { completed_days: number; total_days: number }
  assets_count: number
}

export interface QuestDetailResponse {
  quest: Quest
  days: QuestDaySummary[]
}

export interface ReviewAsset {
  asset_id: string
  asset_type: AssetType
  asset_name: string
}

export interface ReviewData {
  completed_count: number
  total_days: number
  outputs: string[]
  assets: ReviewAsset[]
  observations: string[]
  boss_summary: string
  next_week_suggestion: {
    quest_title: string
    description: string
  }
}

export interface ReviewResponse {
  review: ReviewData
  quest: Pick<Quest, 'quest_id' | 'status' | 'current_day'>
}

export interface NextWeekResponse {
  goal_id: string
  redirect: string
  message: string
}

export interface PauseQuestResponse {
  quest_id: string
  status: QuestStatus
}

export interface AcceptQuestPreview {
  quest_title: string
  success_condition: string
  days: QuestPreviewDay[]
}

export interface AcceptQuestResponse {
  quest: Quest
  today_event: import('./event').DailyEvent
}

export type { Goal }
