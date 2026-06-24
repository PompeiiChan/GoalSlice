import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import App from '@/App'
import { useSessionStore } from '@/stores/sessionStore'
import '@/styles/global.css'

function Bootstrap() {
  const initSession = useSessionStore((s) => s.initSession)

  useEffect(() => {
    initSession()
  }, [initSession])

  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Bootstrap />
  </StrictMode>,
)
