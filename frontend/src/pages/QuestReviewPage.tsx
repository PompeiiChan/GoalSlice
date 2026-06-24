import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { AssetTag } from '@/components/AssetTag'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { DEMO_HEADER_SHORT } from '@/mocks/data'
import { questService } from '@/services/questService'
import { useFlowStore } from '@/stores/flowStore'
import type { ReviewData } from '@/types/quest'
import '@/components/components.css'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function QuestReviewPage() {
  const navigate = useNavigate()
  const [review, setReview] = useState<ReviewData | null>(null)
  const [questId, setQuestId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  usePageHeader({
    variant: 'full',
    centerText: DEMO_HEADER_SHORT,
    progress: { current: 7, total: 7 },
  })

  const setReviewQuestId = useFlowStore((s) => s.setReviewQuestId)

  useEffect(() => {
    const load = async () => {
      try {
        let id = useFlowStore.getState().reviewQuestId
        if (!id) {
          const active = await questService.getActive()
          id = active?.quest.quest_id ?? null
        }
        if (!id) {
          navigate('/')
          return
        }
        setQuestId(id)
        setReviewQuestId(id)
        const data = await questService.review(id)
        setReview(data.review)
      } catch (err) {
        message.error(err instanceof Error ? err.message : '加载复盘失败')
        navigate(useMock ? '/hub' : '/')
      }
    }
    void load()
  }, [navigate, setReviewQuestId])

  const handleNextWeek = async () => {
    if (!questId) return
    setLoading(true)
    try {
      const data = await questService.nextWeek(questId)
      const path = data.redirect === 'clarify' ? '/clarify' : '/'
      navigate(path)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async () => {
    if (!questId) return
    setLoading(true)
    try {
      await questService.pause(questId)
      navigate('/')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '操作失败')
    } finally {
      setLoading(false)
    }
  }

  if (!review) return null

  const assetCounts = review.assets.reduce<Record<string, number>>((acc, a) => {
    acc[a.asset_name] = (acc[a.asset_name] ?? 0) + 1
    return acc
  }, {})

  return (
    <PageContent pageId="P07">
      <div className="card card--boss">
        <div className="card-label">本周 Boss 战 · 已完成</div>
        <h2 className="section-title">{review.boss_summary}</h2>
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{review.completed_count}</div>
          <div className="stat-label">完成小事件</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{review.outputs.length}</div>
          <div className="stat-label">产出物</div>
        </div>
      </div>
      <div className="card">
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 12 }}>本周你推进了</div>
        <ul className="review-list">
          {review.outputs.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>成长资产</div>
        <div className="asset-wall">
          {Object.entries(assetCounts).map(([name, count]) => (
            <AssetTag key={name} name={name} count={count} />
          ))}
        </div>
      </div>
      <div className="observation">{review.observations[0]}</div>
      <div className="card" style={{ borderColor: 'var(--accent)' }}>
        <div className="card-label">下一周建议</div>
        <p style={{ fontSize: 15, fontWeight: 500 }}>{review.next_week_suggestion.quest_title}</p>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 6 }}>
          {review.next_week_suggestion.description}
        </p>
      </div>
      <button type="button" className="btn btn-primary" disabled={loading} onClick={handleNextWeek}>
        开启下一周副本
      </button>
      <button
        type="button"
        className="btn btn-text"
        style={{ width: '100%', marginTop: 12 }}
        disabled={loading}
        onClick={handlePause}
      >
        暂停，下次再说
      </button>
    </PageContent>
  )
}
