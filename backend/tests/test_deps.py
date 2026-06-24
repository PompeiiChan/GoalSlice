"""测试依赖注入。"""

import pytest
from fastapi import HTTPException
from src.api.deps import get_session_id


@pytest.mark.asyncio
async def test_get_session_id_valid() -> None:
    """有效 session_id 应被接受。"""
    session_id = await get_session_id(x_session_id="test-session-123")
    assert session_id == "test-session-123"


@pytest.mark.asyncio
async def test_get_session_id_with_whitespace() -> None:
    """session_id 前后空格应被去除。"""
    session_id = await get_session_id(x_session_id="  test-session-456  ")
    assert session_id == "test-session-456"


@pytest.mark.asyncio
async def test_get_session_id_missing() -> None:
    """缺失 session_id 应抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id(x_session_id=None)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_session_id_empty() -> None:
    """空 session_id 应抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id(x_session_id="")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_session_id_only_whitespace() -> None:
    """纯空格 session_id 应抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id(x_session_id="   ")
    assert exc_info.value.status_code == 400
