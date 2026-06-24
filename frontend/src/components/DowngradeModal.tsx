import { useEffect, useState } from 'react'
import type { DowngradeOption } from '@/types/event'
import './components.css'

interface DowngradeModalProps {
  open: boolean
  options: DowngradeOption[]
  loading?: boolean
  onCancel: () => void
  onConfirm: (optionId: string) => void
}

export function DowngradeModal({ open, options, loading, onCancel, onConfirm }: DowngradeModalProps) {
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    if (open) setSelected(null)
  }, [open])

  if (!open) return null

  const handleConfirm = () => {
    if (selected) onConfirm(selected)
  }

  return (
    <div
      className="modal-overlay active"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div className="modal" role="dialog" aria-modal="true">
        <h3 className="modal-title">帮你缩小今天的任务</h3>
        <p className="modal-desc">选一个你能接受的版本，完成仍算有效推进。</p>
        {options.map((opt) => (
          <button
            key={opt.option_id}
            type="button"
            className={`downgrade-option${selected === opt.option_id ? ' selected' : ''}`}
            onClick={() => setSelected(opt.option_id)}
          >
            <div className="downgrade-option-title">{opt.title}</div>
            <div className="downgrade-option-desc">{opt.description}</div>
          </button>
        ))}
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            取消
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selected || loading}
            onClick={handleConfirm}
          >
            采用这个版本
          </button>
        </div>
      </div>
    </div>
  )
}
