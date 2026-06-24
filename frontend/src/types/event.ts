import type { AssetType, EventStatus, OutputType } from './api'

export interface DailyEvent {
  event_id: string
  quest_id: string
  day_index: number
  event_title: string
  event_description: string
  estimated_time: string
  meaning: string
  output_type: OutputType
  /** 任务操作区输入引导；Demo 用普适默认文案，联调后由 LLM 按任务生成 */
  output_hint?: string | null
  user_output: string | null
  status: EventStatus
  original_event_id: string | null
  completed_at: string | null
}

export interface QuestSummary {
  quest_title: string
  current_day: number
  total_days: number
  completed_days?: number
}

export interface TodayEventResponse {
  event: DailyEvent
  quest_summary: QuestSummary
}

export interface FeedbackAsset {
  asset_id: string
  asset_type: AssetType
  asset_name: string
}

export interface CompleteFeedback {
  completion_title: string
  action_label: string
  meaning_text: string
  asset: FeedbackAsset
  progress: { completed_days: number; total_days: number }
  tomorrow_preview: { day_index: number; event_title: string }
  is_quest_completed: boolean
}

export interface CompleteEventResponse {
  event: DailyEvent
  feedback: CompleteFeedback
}

export interface DowngradeOption {
  option_id: string
  title: string
  description: string
  estimated_time: string
}

export interface DowngradeOptionsResponse {
  options: DowngradeOption[]
}

export interface ApplyDowngradeResponse {
  event: DailyEvent
}
