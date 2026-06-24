"""成长资产 Pydantic 模型 — 对齐 api-contracts.md。"""

from pydantic import BaseModel


class GrowthAssetDTO(BaseModel):
    asset_id: str
    session_id: str
    quest_id: str
    event_id: str
    asset_type: str
    asset_name: str
    asset_content: str | None = None
    created_at: str


class AssetListResponseData(BaseModel):
    items: list[GrowthAssetDTO]
