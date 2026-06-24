import './components.css'

interface AssetTagProps {
  name: string
  count?: number
}

export function AssetTag({ name, count = 1 }: AssetTagProps) {
  return (
    <span className="tag tag-asset">
      {name} ×{count}
    </span>
  )
}
