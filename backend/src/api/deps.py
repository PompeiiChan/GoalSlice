"""FastAPI 依赖注入 — 基于 pycore 模板扩展。"""

from fastapi import Header, HTTPException, status

from src.db.session import get_db

__all__ = ["get_db", "get_session_id"]


async def get_session_id(x_session_id: str | None = Header(None, alias="X-Session-Id")) -> str:
    """
    解析 X-Session-Id 请求头。

    业务接口必须提供有效的 session_id（匿名会话 UUID）。
    """
    if not x_session_id or not x_session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid X-Session-Id header",
        )
    return x_session_id.strip()
