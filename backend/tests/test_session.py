"""测试数据库会话管理（隔离测试库）。"""

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from src.db.models import Base


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """创建临时测试数据库引擎。"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        temp_db_path = Path(temp_db.name)

    engine = create_async_engine(f"sqlite+aiosqlite:///{temp_db_path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()
    temp_db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_session_creation(test_engine: AsyncEngine) -> None:
    """测试会话创建。"""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(test_engine, class_=AsyncSession)

    async with session_maker() as session:
        assert session is not None
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_database_initialization(test_engine: AsyncEngine) -> None:
    """测试数据库表创建。"""
    async with test_engine.begin() as conn:
        result = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "goals")
        )
        assert result is True

        result = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "user_contexts")
        )
        assert result is True

        result = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "quests")
        )
        assert result is True

        result = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "daily_events")
        )
        assert result is True

        result = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "growth_assets")
        )
        assert result is True
