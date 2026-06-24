import './components.css'

interface MeaningBlockProps {
  title?: string
  children: React.ReactNode
}

export function MeaningBlock({ title = '为什么做这一步', children }: MeaningBlockProps) {
  return (
    <div className="meaning-block">
      <div className="meaning-block-title">{title}</div>
      <p>{children}</p>
    </div>
  )
}
