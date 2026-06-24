import './components.css'

interface CompleteHeroProps {
  dayLabel: string
  actionLabel: string
}

export function CompleteHero({ dayLabel, actionLabel }: CompleteHeroProps) {
  return (
    <div className="complete-hero">
      <div className="check-ring">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="#fff"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <div className="complete-title">{dayLabel} 已完成</div>
      <div className="complete-sub">你今天完成的是「{actionLabel}」</div>
    </div>
  )
}
