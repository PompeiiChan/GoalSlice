"""成长资产数据访问层。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import GrowthAsset


class AssetRepository:
    """GrowthAsset 查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_assets(
        self, session_id: str, quest_id: str | None = None
    ) -> list[GrowthAsset]:
        stmt = select(GrowthAsset).where(GrowthAsset.session_id == session_id)
        if quest_id:
            stmt = stmt.where(GrowthAsset.quest_id == quest_id)
        stmt = stmt.order_by(GrowthAsset.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_assets(self, session_id: str, quest_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(GrowthAsset)
            .where(GrowthAsset.session_id == session_id, GrowthAsset.quest_id == quest_id)
        )
        return int(result.scalar_one() or 0)
