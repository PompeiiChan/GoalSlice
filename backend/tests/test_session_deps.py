"""测试 session_id 依赖解析。"""

import pytest
from fastapi import HTTPException
from src.api.deps import get_session_id


async def test_get_session_id_valid() -> None:
    """测试有效 session_id 解析。"""
    session_id = await get_session_id("test-session-uuid")
    assert session_id == "test-session-uuid"


async def test_get_session_id_with_spaces() -> None:
    """测试带空格的 session_id 会被 strip。"""
    session_id = await get_session_id("  test-session-uuid  ")
    assert session_id == "test-session-uuid"


async def test_get_session_id_missing() -> None:
    """测试缺失 session_id 抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id(None)
    assert exc_info.value.status_code == 400
    assert "Missing or invalid" in exc_info.value.detail


async def test_get_session_id_empty() -> None:
    """测试空 session_id 抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id("")
    assert exc_info.value.status_code == 400


async def test_get_session_id_whitespace_only() -> None:
    """测试纯空格 session_id 抛出 400。"""
    with pytest.raises(HTTPException) as exc_info:
        await get_session_id("   ")
    assert exc_info.value.status_code == 400
