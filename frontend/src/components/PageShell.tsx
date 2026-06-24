import type { ReactNode } from 'react'

interface PageShellProps {
  pageId: string
  title: string
  children?: ReactNode
}

export function PageShell({ pageId, title, children }: PageShellProps) {
  return (
    <div className="page-content" data-page={pageId}>
      <h1 className="display-title" style={{ fontSize: 22, marginBottom: 12 }}>
        {title}
      </h1>
      {children ?? <p className="page-placeholder">页面骨架占位 — 业务逻辑将在后续任务实现</p>}
    </div>
  )
}
