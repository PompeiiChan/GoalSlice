import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { AssetTag } from '@/components/AssetTag'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { DEMO_HEADER_SHORT } from '@/mocks/data'
import { assetService } from '@/services/assetService'
import { questService } from '@/services/questService'
import type { ActiveQuestResponse } from '@/types/quest'
import type { GrowthAsset } from '@/types/asset'
import '@/components/components.css'

const RING_CIRCUMFERENCE = 2 * Math.PI * 34

export function HubPage() {
  const navigate = useNavigate()
  const [active, setActive] = useState<ActiveQuestResponse | null>(null)
  const [assets, setAssets] = useState<GrowthAsset[]>([])

  const completed = active?.progress.completed_days ?? 0
  const total = active?.progress.total_days ?? 7
  const offset = RING_CIRCUMFERENCE * (1 - completed / total)

  usePageHeader({
    variant: 'full',
    centerText: DEMO_HEADER_SHORT,
    progress: { current: completed, total },
  })

  useEffect(() => {
    const load = async () => {
      try {
        const data = await questService.getActive()
        if (!data) {
          navigate('/')
          return
        }
        setActive(data)
        const assetData = await assetService.list(data.quest.quest_id)
        setAssets(assetData.items)
      } catch (err) {
        message.error(err instanceof Error ? err.message : '加载失败')
      }
    }
    load()
  }, [navigate])

  if (!active) return null

  const assetCounts = assets.reduce<Record<string, number>>((acc, a) => {
    acc[a.asset_name] = (acc[a.asset_name] ?? 0) + 1
    return acc
  }, {})

  return (
    <PageContent pageId="P08">
      <div className="card hub-card">
        <div className="hub-progress-ring">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="#E5E5EA" strokeWidth="6" />
            <circle
              cx="40"
              cy="40"
              r="34"
              fill="none"
              stroke="#E8463A"
              strokeWidth="6"
              strokeDasharray={RING_CIRCUMFERENCE}
              strokeDashoffset={offset}
              strokeLinecap="round"
            />
          </svg>
          <div className="hub-progress-text">
            {completed}/{total}
          </div>
        </div>
        <p className="card-label">本周主线</p>
        <h2 className="section-title" style={{ fontSize: 18 }}>
          {active.quest.quest_title}
        </h2>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 8 }}>
          通关条件：{active.quest.success_condition}
        </p>
      </div>
      <button type="button" className="btn btn-primary" onClick={() => navigate('/quest/today')}>
        进入今日任务
      </button>
      <div className="card" style={{ marginTop: 20 }}>
        <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 12 }}>已获得的成长资产</div>
        <div className="asset-wall">
          {Object.entries(assetCounts).map(([name, count]) => (
            <AssetTag key={name} name={name} count={count} />
          ))}
        </div>
      </div>
      <button
        type="button"
        className="link-secondary"
        onClick={() => navigate('/quest/preview?readonly=1')}
      >
        查看完整主线 →
      </button>
    </PageContent>
  )
}
