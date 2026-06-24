import { clearMockState } from '@/mocks/storage'
import { useFlowStore } from '@/stores/flowStore'
import { SESSION_STORAGE_KEY, generateSessionId } from '@/utils/session'

/** Demo：清空本机会话与 Mock 进度，相当于全新访客。真实 API 下换新 session_id，后端旧数据仍保留但不再关联。 */
export function resetDemoToStart(): void {
  clearMockState()
  localStorage.removeItem(SESSION_STORAGE_KEY)
  localStorage.setItem(SESSION_STORAGE_KEY, generateSessionId())
  useFlowStore.getState().reset()
}

export function isDemoResetEnabled(): boolean {
  return import.meta.env.VITE_DEMO_RESET === 'true'
}
