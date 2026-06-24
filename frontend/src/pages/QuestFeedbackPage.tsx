import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AssetTag } from '@/components/AssetTag'
import { CompleteHero } from '@/components/CompleteHero'
import { MeaningBlock } from '@/components/MeaningBlock'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { ProgressBar } from '@/components/ProgressBar'
import { DEMO_HEADER_SHORT } from '@/mocks/data'
import { eventService } from '@/services/eventService'
import { useFlowStore } from '@/stores/flowStore'
import '@/components/components.css'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function QuestFeedbackPage() {
  const navigate = useNavigate()
  const lastFeedback = useFlowStore((s) => s.lastFeedback)
  const completedDayIndex = useFlowStore((s) => s.completedDayIndex)

  usePageHeader({
    variant: 'full',
    centerText: DEMO_HEADER_SHORT,
    progress: lastFeedback
      ? { current: lastFeedback.progress.completed_days, total: lastFeedback.progress.total_days }
      : { current: 0, total: 7 },
  })

  useEffect(() => {
    if (!lastFeedback || completedDayIndex === null) {
      navigate('/quest/today', { replace: true })
    }
  }, [lastFeedback, completedDayIndex, navigate])

  if (!lastFeedback || completedDayIndex === null) {
    return null
  }

  const handleDone = () => {
    if (lastFeedback.is_quest_completed) {
      navigate('/quest/review')
      return
    }
    if (useMock) {
      eventService.advanceDayAfterFeedback()
      navigate('/hub')
      return
    }
    navigate('/quest/today')
  }

  return (
    <PageContent pageId="P05">
      <CompleteHero
        dayLabel={`Day ${completedDayIndex}`}
        actionLabel={lastFeedback.action_label}
      />
      <MeaningBlock title="这一步的意义">{lastFeedback.meaning_text}</MeaningBlock>
      <div style={{ margin: '20px 0' }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>获得成长资产</span>
        <div className="asset-wall" style={{ marginTop: 8 }}>
          <AssetTag name={lastFeedback.asset.asset_name} />
        </div>
      </div>
      <ProgressBar
        current={lastFeedback.progress.completed_days}
        total={lastFeedback.progress.total_days}
      />
      {!lastFeedback.is_quest_completed && (
        <div className="tomorrow-preview">
          明天解锁：<strong>{lastFeedback.tomorrow_preview.event_title}</strong>
        </div>
      )}
      <button type="button" className="btn btn-primary" onClick={handleDone}>
        好的，明天见
      </button>
    </PageContent>
  )
}
