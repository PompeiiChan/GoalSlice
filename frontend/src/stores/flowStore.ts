import { create } from 'zustand'
import type { ClarifyQuestion, Goal } from '@/types/goal'
import type { CompleteFeedback } from '@/types/event'
import type { QuestPreview } from '@/types/quest'
import { loadMockState } from '@/mocks/storage'

interface FlowState {
  goal: Goal | null
  goalId: string | null
  clarifyQuestions: ClarifyQuestion[]
  preview: QuestPreview | null
  lastFeedback: CompleteFeedback | null
  completedDayIndex: number | null
  reviewQuestId: string | null
  setGoal: (goal: Goal) => void
  setClarifyQuestions: (questions: ClarifyQuestion[]) => void
  setPreview: (preview: QuestPreview) => void
  setLastFeedback: (feedback: CompleteFeedback, dayIndex: number) => void
  setReviewQuestId: (questId: string) => void
  hydrateFromMock: () => void
  reset: () => void
}

export const useFlowStore = create<FlowState>((set) => ({
  goal: null,
  goalId: null,
  clarifyQuestions: [],
  preview: null,
  lastFeedback: null,
  completedDayIndex: null,
  reviewQuestId: null,
  setGoal: (goal) => set({ goal, goalId: goal.goal_id }),
  setClarifyQuestions: (questions) => set({ clarifyQuestions: questions }),
  setPreview: (preview) => set({ preview }),
  setLastFeedback: (feedback, dayIndex) =>
    set({ lastFeedback: feedback, completedDayIndex: dayIndex }),
  setReviewQuestId: (questId) => set({ reviewQuestId: questId }),
  hydrateFromMock: () => {
    const state = loadMockState()
    set({
      goal: state.goal,
      goalId: state.goal?.goal_id ?? null,
      preview: state.preview,
    })
  },
  reset: () =>
    set({
      goal: null,
      goalId: null,
      clarifyQuestions: [],
      preview: null,
      lastFeedback: null,
      completedDayIndex: null,
      reviewQuestId: null,
    }),
}))
