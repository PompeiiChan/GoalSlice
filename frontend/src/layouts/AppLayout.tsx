import { Outlet } from 'react-router-dom'
import { AppHeader } from '@/components/AppHeader'
import { HeaderProvider, useHeaderConfig } from '@/contexts/HeaderContext'

function AppShell() {
  const { config } = useHeaderConfig()
  return (
    <div className="app-shell">
      <AppHeader
        variant={config.variant}
        centerText={config.centerText}
        progress={config.progress}
      />
      <main>
        <Outlet />
      </main>
    </div>
  )
}

export function AppLayout() {
  return (
    <HeaderProvider>
      <AppShell />
    </HeaderProvider>
  )
}
