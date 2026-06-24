"""成长资产 API 路由。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import success_response
from src.api.deps import get_db, get_session_id
from src.services.asset_service import AssetService

router = APIRouter(tags=["assets"])


async def get_asset_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AssetService:
    return AssetService(db)


@router.get("/assets")
async def list_assets(
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[AssetService, Depends(get_asset_service)],
    quest_id: Annotated[str | None, Query()] = None,
) -> Any:
    data = await service.list_assets(session_id, quest_id)
    return success_response(data.model_dump())
