"""API 路由注册。"""

from fastapi import APIRouter

from src.api.routes import assets, events, goals, quests

router = APIRouter(prefix="/api/v1")
router.include_router(goals.router)
router.include_router(quests.router)
router.include_router(events.router)
router.include_router(assets.router)
