import type { ReactNode } from 'react'
import { MeaningBlock } from './MeaningBlock'
import './components.css'

interface QuestCardProps {
  dayIndex: number
  estimatedTime: string
  title: string
  description: string
  meaning: string
  children?: ReactNode
}

export function QuestCard({
  dayIndex,
  estimatedTime,
  title,
  description,
  meaning,
  children,
}: QuestCardProps) {
  return (
    <>
      <div className="tags-row">
        <span className="tag tag-day">Day {dayIndex}</span>
        <span className="tag tag-time">预计 {estimatedTime}</span>
      </div>
      <div className="card card--quest">
        <h2 className="section-title">{title}</h2>
        <p className="quest-desc">{description}</p>
        <MeaningBlock>{meaning}</MeaningBlock>
        {children}
      </div>
    </>
  )
}
