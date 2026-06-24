"""GoalSlice 数据库初始化脚本。

运行：cd backend && PYTHONPATH=.. python3 scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 确保 backend/ 作为包根
backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from src.db.session import init_db


async def main() -> None:
    """初始化数据库表。"""
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(main())
