import type { AssetType } from './api'

export interface GrowthAsset {
  asset_id: string
  session_id: string
  quest_id: string
  event_id: string
  asset_type: AssetType
  asset_name: string
  asset_content: string | null
  created_at: string
}

export interface AssetListResponse {
  items: GrowthAsset[]
}
