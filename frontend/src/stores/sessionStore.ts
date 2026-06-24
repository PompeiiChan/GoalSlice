import { create } from 'zustand'
import { ensureSessionId, getStoredSessionId, SESSION_STORAGE_KEY } from '@/utils/session'

interface SessionState {
  sessionId: string
  initSession: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: '',
  initSession: () => {
    const id = ensureSessionId()
    set({ sessionId: id })
  },
}))

export { SESSION_STORAGE_KEY, getStoredSessionId }
