"""周复盘 / 开启下周 / 暂停 API 测试。"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.core.quest_templates import build_meeting_summary_preview
from src.db.migrations import apply_sqlite_migrations
from src.db.models import Base, Goal, Quest
from src.main import app
from src.models.event import FeedbackLLMSchema

SESSION_HEADER = "X-Session-Id"
CLARIFY_ANSWERS = {
    "goal_type": "技能提升",
    "weekly_outcome": "完成一个具体产物",
    "available_time": "15 分钟",
    "current_level": "有一点了解，但不系统",
    "failure_reason": "不知道第一步做什么",
}


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


def _create_and_clarify(test_client: TestClient, session_id: str) -> str:
    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升自己的会议总结能力"},
        headers=_headers(session_id),
    )
    goal_id = str(create.json()["data"]["goal"]["goal_id"])
    test_client.patch(
        f"/api/v1/goals/{goal_id}/clarify",
        json={"answers": CLARIFY_ANSWERS},
        headers=_headers(session_id),
    )
    return goal_id


def _accept_quest(test_client: TestClient, session_id: str, goal_id: str) -> str:
    preview = build_meeting_summary_preview()

    async def fake_llm(self: object, goal: object, context: object) -> object:
        return preview

    with patch("src.services.quest_service.QuestService._generate_with_llm", new=fake_llm):
        test_client.post(
            "/api/v1/quests/generate",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
        accept = test_client.post(
            "/api/v1/quests",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
    return str(accept.json()["data"]["quest"]["quest_id"])


def _complete_all_days(test_client: TestClient, session_id: str) -> None:
    async def fake_feedback(self: object, event: object, quest: object) -> FeedbackLLMSchema:
        return FeedbackLLMSchema(
            action_label="测试",
            meaning_text="测试反馈",
            asset_name="总结模板碎片",
            asset_type="template_fragment",
        )

    with patch("src.services.event_service.EventService._generate_feedback", new=fake_feedback):
        for _ in range(7):
            today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
            assert today.status_code == 200
            event_id = today.json()["data"]["event"]["event_id"]
            complete = test_client.post(
                f"/api/v1/events/{event_id}/complete",
                json={},
                headers=_headers(session_id),
            )
            assert complete.status_code == 200


def test_review_quest_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "review-ok"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)
    _complete_all_days(test_client, session_id)

    response = test_client.post(
        f"/api/v1/quests/{quest_id}/review",
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["quest"]["status"] == "completed"
    assert body["review"]["boss_summary"]
    assert body["review"]["next_week_suggestion"]["quest_title"]

    async def verify_db() -> str:
        async with session_maker() as session:
            result = await session.execute(select(Quest).where(Quest.quest_id == quest_id))
            return result.scalar_one().status

    assert asyncio.run(verify_db()) == "completed"


def test_review_quest_not_ready(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "review-not-ready"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)

    response = test_client.post(
        f"/api/v1/quests/{quest_id}/review",
        headers=_headers(session_id),
    )
    assert response.status_code == 422


def test_next_week_after_review(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "next-week-ok"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)
    _complete_all_days(test_client, session_id)
    test_client.post(f"/api/v1/quests/{quest_id}/review", headers=_headers(session_id))

    response = test_client.post(
        f"/api/v1/quests/{quest_id}/next-week",
        json={"accept_suggestion": True},
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["redirect"] == "clarify"
    assert data["goal_id"] == goal_id

    async def verify_goal() -> str:
        async with session_maker() as session:
            result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
            return result.scalar_one().status

    assert asyncio.run(verify_goal()) == "active"


def test_pause_quest(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "pause-ok"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)

    response = test_client.post(
        f"/api/v1/quests/{quest_id}/pause",
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "abandoned"

    active = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert active.json()["data"] is None

    async def verify_goal() -> str:
        async with session_maker() as session:
            result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
            return result.scalar_one().status

    assert asyncio.run(verify_goal()) == "paused"
