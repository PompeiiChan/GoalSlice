import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import { ClarifyOptionCard } from '@/components/ClarifyOptionCard'
import { PageContent, usePageHeader } from '@/components/PageLayout'
import { CLARIFY_QUESTIONS } from '@/constants/clarifyQuestions'
import { goalService } from '@/services/goalService'
import { useFlowStore } from '@/stores/flowStore'
import '@/components/components.css'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

function firstUnansweredStep(answers: Record<string, string>, questions = CLARIFY_QUESTIONS): number {
  const idx = questions.findIndex((q) => !answers[q.question_id])
  return idx === -1 ? questions.length - 1 : idx
}

export function ClarifyPage() {
  const navigate = useNavigate()
  const goalId = useFlowStore((s) => s.goalId)
  const clarifyQuestions = useFlowStore((s) => s.clarifyQuestions)
  const setGoal = useFlowStore((s) => s.setGoal)
  const setClarifyQuestions = useFlowStore((s) => s.setClarifyQuestions)
  const hydrateFromMock = useFlowStore((s) => s.hydrateFromMock)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [selected, setSelected] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [ready, setReady] = useState(false)

  const questions = clarifyQuestions.length > 0 ? clarifyQuestions : CLARIFY_QUESTIONS

  usePageHeader({ variant: 'simple' })

  useEffect(() => {
    let cancelled = false

    const hydrate = async () => {
      if (useMock) {
        hydrateFromMock()
        if (!useFlowStore.getState().goalId) {
          navigate('/', { replace: true })
          return
        }
        setReady(true)
        return
      }

      try {
        const active = await goalService.getActiveGoal()
        if (cancelled) return

        if (!active) {
          navigate('/', { replace: true })
          return
        }

        setGoal(active.goal)
        setClarifyQuestions(active.clarify_questions)
        const restored = active.saved_answers ?? {}
        setAnswers(restored)
        const resumeStep = firstUnansweredStep(restored, active.clarify_questions)
        setStep(resumeStep)
        setSelected(restored[active.clarify_questions[resumeStep]?.question_id] ?? null)

        if (active.context) {
          navigate('/quest/preview', { replace: true })
          return
        }

        setReady(true)
      } catch (err) {
        message.error(err instanceof Error ? err.message : '加载澄清进度失败')
        navigate('/', { replace: true })
      }
    }

    void hydrate()
    return () => {
      cancelled = true
    }
  }, [hydrateFromMock, navigate, setClarifyQuestions, setGoal])

  const question = questions[step]
  const isLast = step === questions.length - 1

  const submitClarify = async (finalAnswers: Record<string, string>) => {
    const id = goalId ?? useFlowStore.getState().goalId
    if (!id) {
      navigate('/')
      return
    }
    setLoading(true)
    try {
      const data = await goalService.clarifyGoal(id, finalAnswers, notes)
      setGoal(data.goal)
      navigate('/quest/preview')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const savePartial = async (partialAnswers: Record<string, string>) => {
    const id = goalId ?? useFlowStore.getState().goalId
    if (!id || useMock) return
    try {
      await goalService.clarifyGoal(id, partialAnswers, notes)
    } catch {
      // 分批保存失败不阻断答题，最终提交仍会校验
    }
  }

  const handleNext = async () => {
    const nextAnswers = { ...answers }
    if (selected) nextAnswers[question.question_id] = selected

    if (!isLast) {
      setAnswers(nextAnswers)
      await savePartial(nextAnswers)
      setStep((s) => s + 1)
      setSelected(nextAnswers[questions[step + 1].question_id] ?? null)
      return
    }

    await submitClarify(nextAnswers)
  }

  const handleBack = () => {
    if (step === 0) {
      navigate('/')
      return
    }
    const currentAnswers = { ...answers }
    if (selected) currentAnswers[question.question_id] = selected
    setAnswers(currentAnswers)
    const prevStep = step - 1
    setStep(prevStep)
    setSelected(currentAnswers[questions[prevStep].question_id] ?? null)
  }

  const handleSkip = () => {
    if (step < questions.length - 1) {
      setStep((s) => s + 1)
      setSelected(answers[questions[step + 1].question_id] ?? null)
      return
    }
    void submitClarify(answers)
  }

  if (!ready || !question) {
    return null
  }

  return (
    <PageContent pageId="P02">
      <button type="button" className="clarify-nav-back" onClick={handleBack}>
        {step === 0 ? '← 返回上一页' : '← 上一题'}
      </button>
      <div className="step-indicator">
        <div className="step-dots">
          {questions.map((_, i) => (
            <span
              key={i}
              className={`step-dot${i === step ? ' active' : ''}${i < step ? ' done' : ''}`}
            />
          ))}
        </div>
        <span className="step-label">
          题 {step + 1}/{questions.length}
        </span>
      </div>
      <h2 className="display-title" style={{ fontSize: 22 }}>
        {question.question}
      </h2>
      <p className="subtitle">选一个最贴近你的选项，也可以跳过。</p>
      <div className="option-list">
        {question.options.map((opt) => (
          <ClarifyOptionCard
            key={opt}
            label={opt}
            selected={selected === opt}
            onSelect={() => setSelected(opt)}
          />
        ))}
      </div>
      <input
        type="text"
        className="input-small"
        placeholder="可选：补充一句你的想法…"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
      <div className="btn-row">
        <button type="button" className="btn btn-secondary" onClick={handleSkip}>
          跳过
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={!selected || loading}
          onClick={handleNext}
        >
          下一题
        </button>
      </div>
    </PageContent>
  )
}
