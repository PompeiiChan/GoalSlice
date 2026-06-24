import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { message } from 'antd'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { DEMO_HEADER_SHORT, DEMO_TOTAL_ESTIMATED } from '@/mocks/data'
import { goalService } from '@/services/goalService'
import { questService } from '@/services/questService'
import { useFlowStore } from '@/stores/flowStore'
import type { QuestPreview, QuestPreviewDay } from '@/types/quest'
import '@/components/components.css'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function QuestPreviewPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const readonly = searchParams.get('readonly') === '1'
  const goalId = useFlowStore((s) => s.goalId)
  const setGoal = useFlowStore((s) => s.setGoal)
  const setPreview = useFlowStore((s) => s.setPreview)
  const hydrateFromMock = useFlowStore((s) => s.hydrateFromMock)
  const [preview, setPreviewLocal] = useState<QuestPreview | null>(useFlowStore.getState().preview)
  const [completedDays, setCompletedDays] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [resolvedGoalId, setResolvedGoalId] = useState<string | null>(goalId)
  const [loadError, setLoadError] = useState<string | null>(null)

  usePageHeader({
    variant: 'full',
    centerText: DEMO_HEADER_SHORT,
    progress: { current: completedDays.length, total: 7 },
  })

  useEffect(() => {
    const load = async () => {
      if (useMock) {
        hydrateFromMock()
      }

      let id = goalId ?? useFlowStore.getState().goalId

      if (!useMock && !id) {
        try {
          const active = await goalService.getActiveGoal()
          if (!active?.context) {
            navigate('/', { replace: true })
            return
          }
          setGoal(active.goal)
          id = active.goal.goal_id
        } catch {
          navigate('/', { replace: true })
          return
        }
      }

      if (!id) {
        if (!readonly) navigate('/')
        return
      }

      setResolvedGoalId(id)

      try {
        if (readonly) {
          const active = await questService.getActive()
          if (active) {
            const detail = await questService.getDetail(active.quest.quest_id)
            const done = detail.days.filter((d) => d.status === 'completed').map((d) => d.day_index)
            setCompletedDays(done)
            setPreviewLocal({
              quest_title: detail.quest.quest_title,
              success_condition: detail.quest.success_condition,
              total_estimated_time: DEMO_TOTAL_ESTIMATED,
              days: detail.days.map((d) => ({
                day_index: d.day_index,
                event_title: d.event_title,
                event_description: '',
                estimated_time: d.estimated_time,
                meaning: '',
                output_type: 'text' as const,
                is_boss: d.is_boss,
              })),
            })
          }
        } else {
          const data = await questService.generatePreview(id)
          setPreview(data.preview)
          setPreviewLocal(data.preview)
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : '加载失败'
        message.error(msg)
        if (msg.includes('MVP') || msg.includes('AI 服务')) {
          setLoadError(msg)
        } else if (!readonly) {
          navigate('/', { replace: true })
        }
      }
    }
    void load()
  }, [goalId, hydrateFromMock, navigate, readonly, setGoal, setPreview])

  const handleAccept = async () => {
    const id = resolvedGoalId ?? goalId ?? useFlowStore.getState().goalId
    if (!id || !preview) return
    setLoading(true)
    try {
      await questService.acceptQuest(id, preview)
      navigate('/quest/today')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '接受计划失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerate = async () => {
    const id = resolvedGoalId ?? goalId ?? useFlowStore.getState().goalId
    if (!id) return
    try {
      const data = await questService.generatePreview(id)
      setPreview(data.preview)
      setPreviewLocal(data.preview)
      message.success('计划已重新生成')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '重新生成失败')
    }
  }

  if (loadError) {
    return (
      <PageContent pageId="P03">
        <h2 className="section-title">暂时无法生成计划</h2>
        <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 24 }}>{loadError}</p>
        <button type="button" className="btn btn-primary" onClick={() => navigate('/clarify')}>
          返回澄清页
        </button>
      </PageContent>
    )
  }

  if (!preview) return null

  return (
    <PageContent pageId="P03">
      <p className="card-label">你的本周主线</p>
      <h2 className="section-title">{preview.quest_title}</h2>
      <div className="card">
        <div className="card-label" style={{ color: 'var(--primary)' }}>
          本周通关条件
        </div>
        <p style={{ fontSize: 15 }}>{preview.success_condition}</p>
      </div>
      <ul className="timeline">
        {preview.days.map((item: QuestPreviewDay) => {
          const done = completedDays.includes(item.day_index)
          const cls = ['timeline-item', done ? 'done' : '', item.is_boss ? 'boss' : '']
            .filter(Boolean)
            .join(' ')
          return (
            <li key={item.day_index} className={cls}>
              <div className="timeline-dot">{item.is_boss ? '★' : item.day_index}</div>
              <div className="timeline-content">
                <div className="timeline-title">
                  {item.is_boss ? 'Boss 战 · ' : ''}
                  {item.event_title}
                </div>
                <div className="timeline-desc">预计 {item.estimated_time}</div>
              </div>
            </li>
          )
        })}
      </ul>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 24 }}>
        预计总投入：{preview.total_estimated_time}
      </p>
      {!readonly && (
        <>
          <button
            type="button"
            className="btn btn-primary"
            disabled={loading}
            onClick={handleAccept}
          >
            开始 Day 1
          </button>
          <button
            type="button"
            className="btn btn-text"
            style={{ width: '100%', marginTop: 12 }}
            onClick={handleRegenerate}
          >
            重新生成计划
          </button>
        </>
      )}
    </PageContent>
  )
}
