"""Event API 路由。"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import success_response
from src.api.deps import get_db, get_session_id
from src.models.event import ApplyDowngradeRequest, CompleteEventRequest, DowngradeRequest
from src.services.event_service import (
    EventBadRequestError,
    EventConflictError,
    EventNotFoundError,
    EventService,
)

router = APIRouter(tags=["events"])


def _error_json(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None},
    )


async def get_event_service(db: Annotated[AsyncSession, Depends(get_db)]) -> EventService:
    return EventService(db)


@router.get("/events/today")
async def get_today_event(
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> Any:
    try:
        data = await service.get_today(session_id)
        return success_response(data.model_dump())
    except EventNotFoundError as exc:
        return _error_json(str(exc), 404)


@router.post("/events/{event_id}/complete")
async def complete_event(
    event_id: str,
    body: CompleteEventRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> Any:
    try:
        data = await service.complete_event(session_id, event_id, body.user_output)
        return success_response(data.model_dump())
    except EventNotFoundError as exc:
        return _error_json(str(exc), 404)
    except EventConflictError as exc:
        return _error_json(str(exc), 422)


@router.post("/events/{event_id}/downgrade")
async def request_downgrade(
    event_id: str,
    body: DowngradeRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> Any:
    try:
        data = await service.request_downgrade(session_id, event_id, body.reason)
        return success_response(data.model_dump())
    except EventNotFoundError as exc:
        return _error_json(str(exc), 404)
    except EventConflictError as exc:
        return _error_json(str(exc), 422)


@router.patch("/events/{event_id}/apply-downgrade")
async def apply_downgrade(
    event_id: str,
    body: ApplyDowngradeRequest,
    session_id: Annotated[str, Depends(get_session_id)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> Any:
    try:
        data = await service.apply_downgrade(session_id, event_id, body.option_id)
        return success_response(data.model_dump())
    except EventNotFoundError as exc:
        return _error_json(str(exc), 404)
    except EventConflictError as exc:
        return _error_json(str(exc), 422)
    except EventBadRequestError as exc:
        return _error_json(str(exc), 400)
