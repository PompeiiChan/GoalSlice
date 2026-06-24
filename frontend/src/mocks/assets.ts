import type { ApiResponse } from '@/types/api'
import type { AssetListResponse } from '@/types/asset'
import { loadMockState } from './storage'

export function mockListAssets(questId?: string): ApiResponse<AssetListResponse> {
  const state = loadMockState()
  const items = questId
    ? state.assets.filter((a) => a.quest_id === questId)
    : state.assets
  return { code: 200, message: 'success', data: { items } }
}
