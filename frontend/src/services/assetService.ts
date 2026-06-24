import type { ApiResponse } from '@/types/api'
import type { AssetListResponse } from '@/types/asset'
import { mockListAssets } from '@/mocks'

const useMock = import.meta.env.VITE_USE_MOCK === 'true'

function assertOk<T>(res: ApiResponse<T>): T {
  if (res.code !== 200 || res.data === null) {
    throw new Error(res.message || '请求失败')
  }
  return res.data
}

export const assetService = {
  async list(questId?: string): Promise<AssetListResponse> {
    if (useMock) {
      return assertOk(mockListAssets(questId))
    }
    const { default: api } = await import('./api')
    const { data } = await api.get<ApiResponse<AssetListResponse>>('/v1/assets', {
      params: questId ? { quest_id: questId } : undefined,
    })
    return assertOk(data)
  },
}
