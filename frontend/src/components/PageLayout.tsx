import { useEffect, type ReactNode } from 'react'
import { useHeaderConfig, type HeaderConfig } from '@/contexts/HeaderContext'

export function usePageHeader(config: HeaderConfig) {
  const { setConfig } = useHeaderConfig()
  const progressCurrent = config.progress?.current
  const progressTotal = config.progress?.total

  useEffect(() => {
    setConfig(config)
    return () => setConfig({ variant: 'simple' })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- header fields tracked individually
  }, [config.variant, config.centerText, progressCurrent, progressTotal, setConfig])
}

export function PageContent({ children, pageId }: { children: ReactNode; pageId: string }) {
  return (
    <div className="page-content" data-page={pageId}>
      {children}
    </div>
  )
}
