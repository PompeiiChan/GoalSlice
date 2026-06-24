import type { AvailableTime, GoalStatus, GoalType } from './api'

export interface Goal {
  goal_id: string
  session_id: string
  raw_goal: string
  goal_type: GoalType | null
  refined_goal: string | null
  weekly_outcome: string | null
  status: GoalStatus
  created_at: string
  updated_at: string
}

export interface ClarifyQuestion {
  question_id: string
  question: string
  options: string[]
}

export interface UserContext {
  session_id: string
  goal_type: GoalType
  weekly_outcome: string
  available_time: AvailableTime
  current_level: string
  failure_reason: string
  preferred_intensity: string
  notes: string
}

export interface CreateGoalResponse {
  goal: Goal
  clarify_questions: ClarifyQuestion[]
}

export interface ClarifyGoalResponse {
  goal: Goal
  context: UserContext
}

export interface ActiveGoalResponse {
  goal: Goal
  clarify_questions: ClarifyQuestion[]
  saved_answers: Record<string, string>
  context: UserContext | null
}
