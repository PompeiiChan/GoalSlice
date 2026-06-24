import './components.css'

interface ProgressBarProps {
  current: number
  total: number
  variant?: 'header' | 'track'
  label?: string
}

export function ProgressBar({ current, total, variant = 'track', label }: ProgressBarProps) {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0

  if (variant === 'header') {
    return (
      <div className="progress-header">
        <span className="progress-text">
          {current}/{total}
        </span>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
        </div>
      </div>
    )
  }

  return (
    <div className="progress-section">
      <div className="progress-label">
        <span>{label ?? '本周进度'}</span>
        <span>
          {current} / {total}
        </span>
      </div>
      <div className="progress-track">
        <div className="progress-track-fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}
