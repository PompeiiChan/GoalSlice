"""Goal API 测试（隔离测试库）。"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.migrations import apply_sqlite_migrations
from src.db.models import Base, Quest
from src.main import app

SESSION_HEADER = "X-Session-Id"


@pytest.fixture
def client() -> Generator[tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]], None, None]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as temp_db:
        temp_db_path = Path(temp_db.name)

    engine = create_async_engine(f"sqlite+aiosqlite:///{temp_db_path}", echo=False)

    async def setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(apply_sqlite_migrations)

    asyncio.run(setup())
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, engine, session_maker

    app.dependency_overrides.clear()

    async def teardown() -> None:
        await engine.dispose()

    asyncio.run(teardown())
    temp_db_path.unlink(missing_ok=True)


def _headers(session_id: str) -> dict[str, str]:
    return {SESSION_HEADER: session_id}


def test_create_goal_success(client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]]) -> None:
    test_client, _, _ = client
    response = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升自己的会议总结能力"},
        headers=_headers("session-create"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["goal"]["raw_goal"] == "我想提升自己的会议总结能力"
    assert len(body["data"]["clarify_questions"]) == 5


def test_create_goal_empty_raw_goal(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    response = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": ""},
        headers=_headers("session-empty"),
    )
    assert response.status_code == 400
    assert response.json()["message"] == "raw_goal 不能为空"


def test_create_goal_conflict_when_quest_in_progress(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "session-conflict"

    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "第一个目标"},
        headers=_headers(session_id),
    )
    goal_id = create.json()["data"]["goal"]["goal_id"]

    async def seed_quest() -> None:
        async with session_maker() as session:
            session.add(
                Quest(
                    quest_id="q-conflict-1",
                    goal_id=goal_id,
                    quest_title="进行中副本",
                    success_condition="完成",
                    status="in_progress",
                )
            )
            await session.commit()

    asyncio.run(seed_quest())

    response = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "第二个目标"},
        headers=_headers(session_id),
    )
    assert response.status_code == 422
    assert "进行中" in response.json()["message"]


def test_clarify_goal_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "session-clarify"

    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升自己的会议总结能力"},
        headers=_headers(session_id),
    )
    goal_id = create.json()["data"]["goal"]["goal_id"]

    response = test_client.patch(
        f"/api/v1/goals/{goal_id}/clarify",
        json={
            "answers": {
                "goal_type": "技能提升",
                "weekly_outcome": "完成一个具体产物",
                "available_time": "15 分钟",
                "current_level": "有一点了解，但不系统",
                "failure_reason": "不知道第一步做什么",
            },
            "notes": "补充说明",
        },
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["goal"]["refined_goal"] == "提升会议总结能力"
    assert body["data"]["context"]["available_time"] == "15m"


def test_clarify_goal_not_found(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    response = test_client.patch(
        "/api/v1/goals/missing-id/clarify",
        json={"answers": {"goal_type": "技能提升"}},
        headers=_headers("session-missing"),
    )
    assert response.status_code == 404


def test_get_active_goal_with_saved_answers(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "session-active"

    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升自己的复盘能力"},
        headers=_headers(session_id),
    )
    goal_id = create.json()["data"]["goal"]["goal_id"]

    test_client.patch(
        f"/api/v1/goals/{goal_id}/clarify",
        json={"answers": {"goal_type": "技能提升", "weekly_outcome": "完成一个具体产物"}},
        headers=_headers(session_id),
    )

    response = test_client.get("/api/v1/goals/active", headers=_headers(session_id))
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["goal"]["goal_id"] == goal_id
    assert body["data"]["saved_answers"]["goal_type"] == "技能提升"
    assert len(body["data"]["clarify_questions"]) == 5
