"""Quest API 路由。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import success_response
from src.api.deps import get_db, get_session_id
from src.models.quest import (
    AcceptQuestRequest,
    GenerateQuestRequest,
    NextWeekRequest,
    QuestPreviewDTO,
)
from src.services.goal_service import GoalConflictError, GoalNotFoundError
from src.services.quest_service import (
    LLMUnavailableError,
    QuestConflictError,
    QuestNotFoundError,
    QuestOutOfScopeError,
    QuestService,
    ValueNotFoundError,
)

router = APIRouter(tags=["quests"])


def _error_json(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
    )


async def get_quest_service(db: Annotated[AsyncSession, Depends(get_db)]) -> QuestService:
    return QuestService(db)


@router.post("/quests/generate")
async def generate_quest(
    body: GenerateQuestRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    try:
        data = await service.generate_preview(session_id, body.goal_id)
        return success_response(data.model_dump())
    except GoalNotFoundError as exc:
        return _error_json(str(exc), 404)
    except ValueNotFoundError as exc:
        return _error_json(str(exc), 404)
    except QuestOutOfScopeError as exc:
        return _error_json(str(exc), 422)
    except LLMUnavailableError:
        return _error_json("AI 服务暂时不可用，请稍后重试", 503)


@router.post("/quests")
async def accept_quest(
    body: AcceptQuestRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    preview_input: QuestPreviewDTO | None = None
    if body.preview is not None:
        preview_input = QuestPreviewDTO(
            quest_title=body.preview.quest_title,
            success_condition=body.preview.success_condition,
            total_estimated_time="每天约 15–30 分钟，共 7 天",
            days=body.preview.days,
        )

    try:
        data = await service.accept_quest(session_id, body.goal_id, preview_input)
        return success_response(data.model_dump())
    except GoalNotFoundError as exc:
        return _error_json(str(exc), 404)
    except ValueNotFoundError as exc:
        return _error_json(str(exc), 404)
    except GoalConflictError as exc:
        return _error_json(str(exc), 422)


@router.get("/quests/active")
async def get_active_quest(
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    data = await service.get_active_quest(session_id)
    return success_response(data.model_dump() if data else None)


@router.get("/quests/{quest_id}")
async def get_quest_detail(
    quest_id: str,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    try:
        data = await service.get_quest_detail(session_id, quest_id)
        return success_response(data.model_dump())
    except QuestNotFoundError as exc:
        return _error_json(str(exc), 404)


@router.post("/quests/{quest_id}/review")
async def review_quest(
    quest_id: str,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    try:
        data = await service.generate_review(session_id, quest_id)
        return success_response(data.model_dump())
    except QuestNotFoundError as exc:
        return _error_json(str(exc), 404)
    except QuestConflictError as exc:
        return _error_json(str(exc), 422)


@router.post("/quests/{quest_id}/next-week")
async def next_week_quest(
    quest_id: str,
    body: NextWeekRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    try:
        data = await service.start_next_week(session_id, quest_id, body.accept_suggestion)
        return success_response(data.model_dump())
    except GoalNotFoundError as exc:
        return _error_json(str(exc), 404)
    except QuestNotFoundError as exc:
        return _error_json(str(exc), 404)
    except QuestConflictError as exc:
        return _error_json(str(exc), 422)


@router.post("/quests/{quest_id}/pause")
async def pause_quest(
    quest_id: str,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[QuestService, Depends(get_quest_service)],
) -> Any:
    try:
        data = await service.pause_quest(session_id, quest_id)
        return success_response(data.model_dump())
    except QuestNotFoundError as exc:
        return _error_json(str(exc), 404)
    except QuestConflictError as exc:
        return _error_json(str(exc), 422)
