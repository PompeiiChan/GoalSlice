import './components.css'

interface ClarifyOptionCardProps {
  label: string
  selected: boolean
  onSelect: () => void
}

export function ClarifyOptionCard({ label, selected, onSelect }: ClarifyOptionCardProps) {
  return (
    <button
      type="button"
      className={`option-card${selected ? ' selected' : ''}`}
      onClick={onSelect}
    >
      {label}
    </button>
  )
}
