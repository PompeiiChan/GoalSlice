import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'

export interface HeaderConfig {
  variant: 'simple' | 'full'
  centerText?: string
  progress?: { current: number; total: number }
}

const defaultConfig: HeaderConfig = { variant: 'simple' }

const HeaderContext = createContext<{
  config: HeaderConfig
  setConfig: (config: HeaderConfig) => void
}>({
  config: defaultConfig,
  setConfig: () => undefined,
})

export function HeaderProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<HeaderConfig>(defaultConfig)
  const value = useMemo(() => ({ config, setConfig }), [config])
  return <HeaderContext.Provider value={value}>{children}</HeaderContext.Provider>
}

export function useHeaderConfig() {
  return useContext(HeaderContext)
}
