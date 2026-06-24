export const SESSION_STORAGE_KEY = 'session_id'

export function generateSessionId(): string {
  return crypto.randomUUID()
}

export function getStoredSessionId(): string | null {
  return localStorage.getItem(SESSION_STORAGE_KEY)
}

export function ensureSessionId(): string {
  const existing = getStoredSessionId()
  if (existing) {
    return existing
  }
  const id = generateSessionId()
  localStorage.setItem(SESSION_STORAGE_KEY, id)
  return id
}
