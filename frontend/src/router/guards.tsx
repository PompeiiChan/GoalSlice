import { useEffect, useState, type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { hasActiveQuest, loadMockState } from '@/mocks'
import { questService } from '@/services/questService'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function HomeRouteGuard({ children }: { children: ReactNode }) {
  const [checking, setChecking] = useState(true)
  const [redirect, setRedirect] = useState(false)

  useEffect(() => {
    const check = async () => {
      if (useMock) {
        setRedirect(hasActiveQuest())
        setChecking(false)
        return
      }
      try {
        const active = await questService.getActive()
        setRedirect(!!active)
      } catch {
        setRedirect(false)
      } finally {
        setChecking(false)
      }
    }
    void check()
  }, [])

  if (checking) return null
  if (redirect) return <Navigate to="/hub" replace />
  return <>{children}</>
}

export function HubRouteGuard({ children }: { children: ReactNode }) {
  const [checking, setChecking] = useState(true)
  const [redirect, setRedirect] = useState(false)

  useEffect(() => {
    const check = async () => {
      if (useMock) {
        setRedirect(!hasActiveQuest())
        setChecking(false)
        return
      }
      try {
        const active = await questService.getActive()
        setRedirect(!active)
      } catch {
        setRedirect(true)
      } finally {
        setChecking(false)
      }
    }
    void check()
  }, [])

  if (checking) return null
  if (redirect) return <Navigate to="/" replace />
  return <>{children}</>
}

export function QuestFlowGuard({ children }: { children: ReactNode }) {
  const [checking, setChecking] = useState(true)
  const [redirect, setRedirect] = useState(false)

  useEffect(() => {
    const check = async () => {
      if (useMock) {
        const state = loadMockState()
        const allowed = hasActiveQuest(state) || (state.reviewGenerated && !!state.review)
        setRedirect(!allowed)
        setChecking(false)
        return
      }
      try {
        const active = await questService.getActive()
        setRedirect(!active)
      } catch {
        setRedirect(true)
      } finally {
        setChecking(false)
      }
    }
    void check()
  }, [])

  if (checking) return null
  if (redirect) return <Navigate to="/" replace />
  return <>{children}</>
}
