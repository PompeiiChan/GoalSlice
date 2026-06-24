"""成长资产服务。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import GrowthAsset
from src.models.asset import AssetListResponseData, GrowthAssetDTO
from src.repositories.asset_repository import AssetRepository


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _asset_to_dto(asset: GrowthAsset) -> GrowthAssetDTO:
    return GrowthAssetDTO(
        asset_id=asset.asset_id,
        session_id=asset.session_id,
        quest_id=asset.quest_id,
        event_id=asset.event_id,
        asset_type=asset.asset_type,
        asset_name=asset.asset_name,
        asset_content=asset.asset_content,
        created_at=_iso_z(asset.created_at),
    )


class AssetService:
    """成长资产列表查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = AssetRepository(session)

    async def list_assets(
        self, session_id: str, quest_id: str | None = None
    ) -> AssetListResponseData:
        assets = await self.repo.list_assets(session_id, quest_id)
        return AssetListResponseData(items=[_asset_to_dto(a) for a in assets])
