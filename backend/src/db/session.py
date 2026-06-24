"""GoalSlice 数据库会话管理 — 基于 pycore 模板扩展。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pycore.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger()

settings = get_settings()
DATABASE_URL = settings.database_url

# SQLite 路径规范化：相对路径解析为绝对路径并创建父目录
if DATABASE_URL.startswith("sqlite"):
    # 提取路径部分（去掉 sqlite+aiosqlite:/// 前缀）
    prefix = "sqlite+aiosqlite:///"
    if DATABASE_URL.startswith(prefix):
        db_path_str = DATABASE_URL[len(prefix) :]
        if not db_path_str.startswith("/"):
            # 相对路径，解析为项目根目录下的绝对路径
            project_root = Path(__file__).resolve().parents[3]
            db_path = project_root / db_path_str
            db_path.parent.mkdir(parents=True, exist_ok=True)
            DATABASE_URL = f"{prefix}{db_path}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于 FastAPI Depends）。"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """上下文管理器形式的数据库会话。"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库（创建表 + 幂等迁移补列）。"""
    from src.db.migrations import apply_sqlite_migrations
    from src.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if DATABASE_URL.startswith("sqlite"):
            await conn.run_sync(apply_sqlite_migrations)
    logger.info("Database initialized")


async def close_db() -> None:
    """关闭数据库连接。"""
    await engine.dispose()
    logger.info("Database connection closed")
