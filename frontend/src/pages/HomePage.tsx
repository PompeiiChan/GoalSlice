import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { EXAMPLE_CHIPS } from '@/mocks'
import { goalService } from '@/services/goalService'
import { useFlowStore } from '@/stores/flowStore'
import '@/components/components.css'

export function HomePage() {
  const navigate = useNavigate()
  const setGoal = useFlowStore((s) => s.setGoal)
  const setClarifyQuestions = useFlowStore((s) => s.setClarifyQuestions)
  const [rawGoal, setRawGoal] = useState('')
  const [loading, setLoading] = useState(false)

  usePageHeader({ variant: 'simple' })

  const handleStart = async () => {
    if (!rawGoal.trim()) return
    setLoading(true)
    try {
      const data = await goalService.createGoal(rawGoal.trim())
      setGoal(data.goal)
      setClarifyQuestions(data.clarify_questions)
      navigate('/clarify')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '创建目标失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageContent pageId="P01">
      <h1 className="display-title">把长期目标，变成这一周能完成的小事件。</h1>
      <p className="subtitle">每天一件事，低压力推进你的职业成长。</p>
      <textarea
        className="textarea"
        placeholder="你最近最想推进的一件职业成长目标是什么？"
        rows={4}
        value={rawGoal}
        onChange={(e) => setRawGoal(e.target.value)}
      />
      <div className="chips">
        {EXAMPLE_CHIPS.map((chip) => (
          <button
            key={chip.label}
            type="button"
            className="chip"
            onClick={() => setRawGoal(chip.goal)}
          >
            {chip.label}
          </button>
        ))}
      </div>
      <button
        type="button"
        className="btn btn-primary"
        disabled={!rawGoal.trim() || loading}
        onClick={handleStart}
      >
        开始拆解
      </button>
      <button type="button" className="link-secondary" onClick={() => navigate('/hub')}>
        继续本周副本 →
      </button>
    </PageContent>
  )
}
