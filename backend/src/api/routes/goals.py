"""Goal API 路由。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import success_response
from src.api.deps import get_db, get_session_id
from src.models.goal import ClarifyAnswersRequest, CreateGoalRequest
from src.services.goal_service import GoalConflictError, GoalNotFoundError, GoalService

router = APIRouter(tags=["goals"])


def _error_json(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
    )


async def get_goal_service(db: Annotated[AsyncSession, Depends(get_db)]) -> GoalService:
    return GoalService(db)


@router.post("/goals")
async def create_goal(
    body: CreateGoalRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[GoalService, Depends(get_goal_service)],
) -> Any:
    try:
        data = await service.create_goal(session_id, body.raw_goal)
        return success_response(data.model_dump())
    except ValueError as exc:
        return _error_json(str(exc), 400)
    except GoalConflictError as exc:
        return _error_json(str(exc), 422)


@router.patch("/goals/{goal_id}/clarify")
async def clarify_goal(
    goal_id: str,
    body: ClarifyAnswersRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[GoalService, Depends(get_goal_service)],
) -> Any:
    try:
        data = await service.clarify_goal(session_id, goal_id, body.answers, body.notes)
        return success_response(data.model_dump())
    except GoalNotFoundError as exc:
        return _error_json(str(exc), 404)


@router.get("/goals/active")
async def get_active_goal(
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[GoalService, Depends(get_goal_service)],
) -> Any:
    data = await service.get_active_goal(session_id)
    if data is None:
        return _error_json("目标不存在", 404)
    return success_response(data.model_dump())
