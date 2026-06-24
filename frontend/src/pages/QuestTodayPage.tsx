import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { DowngradeModal } from '@/components/DowngradeModal'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { QuestCard } from '@/components/QuestCard'
import { DEMO_HEADER_SHORT, DEFAULT_TASK_OUTPUT_HINT } from '@/mocks/data'
import { eventService } from '@/services/eventService'
import { useFlowStore } from '@/stores/flowStore'
import type { DowngradeOption, TodayEventResponse } from '@/types/event'
import '@/components/components.css'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function QuestTodayPage() {
  const navigate = useNavigate()
  const setLastFeedback = useFlowStore((s) => s.setLastFeedback)
  const [today, setToday] = useState<TodayEventResponse | null>(null)
  const [userOutput, setUserOutput] = useState('')
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [downgradeOptions, setDowngradeOptions] = useState<DowngradeOption[]>([])
  const [downgradeLoading, setDowngradeLoading] = useState(false)

  const completed =
    today?.quest_summary.completed_days ??
    (today ? Math.max(0, today.quest_summary.current_day - 1) : 0)

  usePageHeader({
    variant: 'full',
    centerText: today?.quest_summary.quest_title ?? DEMO_HEADER_SHORT,
    progress: { current: completed, total: today?.quest_summary.total_days ?? 7 },
  })

  const loadToday = useCallback(async () => {
    try {
      const data = await eventService.getToday()
      setToday(data)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '加载今日任务失败')
      navigate(useMock ? '/hub' : '/')
    }
  }, [navigate])

  useEffect(() => {
    void loadToday()
  }, [loadToday])

  const handleComplete = async () => {
    if (!today) return
    setLoading(true)
    try {
      const output =
        today.event.output_type === 'checkbox' ? '已完成' : userOutput
      const data = await eventService.complete(today.event.event_id, output || undefined)
      setLastFeedback(data.feedback, today.event.day_index)
      navigate('/quest/feedback')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDowngrade = async () => {
    if (!today) return
    try {
      const data = await eventService.getDowngradeOptions(today.event.event_id)
      setDowngradeOptions(data.options)
      setModalOpen(true)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '获取降级方案失败')
    }
  }

  const handleApplyDowngrade = async (optionId: string) => {
    if (!today) return
    setDowngradeLoading(true)
    try {
      if (optionId === 'tomorrow') {
        setModalOpen(false)
        message.info('明天从原任务继续')
        return
      }
      await eventService.applyDowngrade(today.event.event_id, optionId)
      setModalOpen(false)
      await loadToday()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '应用降级失败')
    } finally {
      setDowngradeLoading(false)
    }
  }

  if (!today) return null

  const { event } = today

  return (
    <PageContent pageId="P04">
      <QuestCard
        dayIndex={event.day_index}
        estimatedTime={event.estimated_time}
        title={event.event_title}
        description={event.event_description}
        meaning={event.meaning}
      >
        {event.output_type === 'text' ? (
          <textarea
            className="textarea"
            style={{ minHeight: 80 }}
            placeholder={event.output_hint ?? DEFAULT_TASK_OUTPUT_HINT}
            value={userOutput}
            onChange={(e) => setUserOutput(e.target.value)}
          />
        ) : null}
      </QuestCard>
      <button type="button" className="btn btn-primary" disabled={loading} onClick={handleComplete}>
        我已经完成
      </button>
      <button
        type="button"
        className="btn btn-text btn-text--warning"
        style={{ width: '100%' }}
        onClick={handleOpenDowngrade}
      >
        今天太难了，帮我降级
      </button>
      <DowngradeModal
        open={modalOpen}
        options={downgradeOptions}
        loading={downgradeLoading}
        onCancel={() => setModalOpen(false)}
        onConfirm={handleApplyDowngrade}
      />
    </PageContent>
  )
}
