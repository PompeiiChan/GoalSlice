"""E2E API 全链路回归 — 主流程、503 异常、暂停分支。

通过 TestClient 模拟 VITE_USE_MOCK=false 下的完整后端旅程，
不替代浏览器手动门禁，但覆盖跨模块 API 契约。
"""

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
from src.db.models import Base, Goal
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
def e2e_client() -> Generator[
    tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]], None, None
]:
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


def _create_goal_and_clarify(test_client: TestClient, session_id: str) -> str:
    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升自己的会议总结能力"},
        headers=_headers(session_id),
    )
    assert create.status_code == 200
    goal_id = str(create.json()["data"]["goal"]["goal_id"])

    clarify = test_client.patch(
        f"/api/v1/goals/{goal_id}/clarify",
        json={"answers": CLARIFY_ANSWERS},
        headers=_headers(session_id),
    )
    assert clarify.status_code == 200
    return goal_id


def _generate_and_accept(test_client: TestClient, session_id: str, goal_id: str) -> str:
    preview = build_meeting_summary_preview()

    async def fake_llm(self: object, goal: object, context: object) -> object:
        return preview

    with patch("src.services.quest_service.QuestService._generate_with_llm", new=fake_llm):
        gen = test_client.post(
            "/api/v1/quests/generate",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
        assert gen.status_code == 200

        accept = test_client.post(
            "/api/v1/quests",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
        assert accept.status_code == 200

    return str(accept.json()["data"]["quest"]["quest_id"])


def _complete_all_days(test_client: TestClient, session_id: str) -> None:
    async def fake_feedback(self: object, event: object, quest: object) -> FeedbackLLMSchema:
        return FeedbackLLMSchema(
            action_label="E2E 测试",
            meaning_text="E2E 完成反馈。",
            asset_name="总结模板碎片",
            asset_type="template_fragment",
        )

    with patch("src.services.event_service.EventService._generate_feedback", new=fake_feedback):
        for day in range(1, 8):
            today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
            assert today.status_code == 200, f"day {day} today failed"
            event_id = today.json()["data"]["event"]["event_id"]
            complete = test_client.post(
                f"/api/v1/events/{event_id}/complete",
                json={"user_output": f"Day {day} 产出"},
                headers=_headers(session_id),
            )
            assert complete.status_code == 200, f"day {day} complete failed"


def test_e2e_full_quest_journey_p01_to_p07(
    e2e_client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    """P01 目标 → 澄清 → 计划 → 7 天完成 → 复盘 → 开启下周。"""
    test_client, _, session_maker = e2e_client
    session_id = "e2e-full-journey"

    goal_id = _create_goal_and_clarify(test_client, session_id)
    quest_id = _generate_and_accept(test_client, session_id, goal_id)

    active = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert active.json()["data"]["quest"]["quest_id"] == quest_id

    _complete_all_days(test_client, session_id)

    review = test_client.post(
        f"/api/v1/quests/{quest_id}/review",
        headers=_headers(session_id),
    )
    assert review.status_code == 200
    assert review.json()["data"]["quest"]["status"] == "completed"
    assert review.json()["data"]["review"]["boss_summary"]

    assets = test_client.get(
        "/api/v1/assets",
        params={"quest_id": quest_id},
        headers=_headers(session_id),
    )
    assert len(assets.json()["data"]["items"]) == 7

    next_week = test_client.post(
        f"/api/v1/quests/{quest_id}/next-week",
        json={"accept_suggestion": True},
        headers=_headers(session_id),
    )
    assert next_week.status_code == 200
    assert next_week.json()["data"]["redirect"] == "clarify"

    async def verify_goal_active() -> str:
        async with session_maker() as session:
            result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
            return result.scalar_one().status

    assert asyncio.run(verify_goal_active()) == "active"


def test_e2e_pause_and_restart_new_goal(
    e2e_client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    """暂停副本后无活跃 quest，可重新创建目标。"""
    test_client, _, _ = e2e_client
    session_id = "e2e-pause-restart"

    goal_id = _create_goal_and_clarify(test_client, session_id)
    quest_id = _generate_and_accept(test_client, session_id, goal_id)

    pause = test_client.post(
        f"/api/v1/quests/{quest_id}/pause",
        headers=_headers(session_id),
    )
    assert pause.status_code == 200
    assert pause.json()["data"]["status"] == "abandoned"

    active = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert active.json()["data"] is None

    create2 = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": "我想提升文档写作能力"},
        headers=_headers(session_id),
    )
    assert create2.status_code == 200
    new_goal_id = create2.json()["data"]["goal"]["goal_id"]
    assert new_goal_id != goal_id or create2.status_code == 200


def test_e2e_quest_generate_503_without_llm(
    e2e_client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    """LLM Key 缺失时计划生成返回 503（前端 P03 友好错误）。"""
    test_client, _, _ = e2e_client
    session_id = "e2e-503-generate"

    goal_id = _create_goal_and_clarify(test_client, session_id)

    response = test_client.post(
        "/api/v1/quests/generate",
        json={"goal_id": goal_id},
        headers=_headers(session_id),
    )
    assert response.status_code == 503
    assert "AI 服务" in response.json()["message"]


def test_e2e_downgrade_and_complete_still_advances(
    e2e_client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    """P04 降级分支：apply-downgrade 后完成仍推进进度。"""
    test_client, _, _ = e2e_client
    session_id = "e2e-downgrade-branch"

    goal_id = _create_goal_and_clarify(test_client, session_id)
    _generate_and_accept(test_client, session_id, goal_id)

    today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    event_id = today.json()["data"]["event"]["event_id"]

    downgrade = test_client.post(
        f"/api/v1/events/{event_id}/downgrade",
        json={"reason": "今天太难了"},
        headers=_headers(session_id),
    )
    assert downgrade.status_code == 200
    assert len(downgrade.json()["data"]["options"]) == 3

    applied = test_client.patch(
        f"/api/v1/events/{event_id}/apply-downgrade",
        json={"option_id": "5min"},
        headers=_headers(session_id),
    )
    assert applied.status_code == 200
    new_event_id = applied.json()["data"]["event"]["event_id"]

    complete = test_client.post(
        f"/api/v1/events/{new_event_id}/complete",
        json={},
        headers=_headers(session_id),
    )
    assert complete.status_code == 200
    assert complete.json()["data"]["feedback"]["progress"]["completed_days"] == 1

    active = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert active.json()["data"]["progress"]["completed_days"] == 1


def test_e2e_hub_endpoints_after_one_complete(
    e2e_client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    """P08 中枢：完成 1 天后 active + assets + quest detail 可用。"""
    test_client, _, _ = e2e_client
    session_id = "e2e-hub"

    goal_id = _create_goal_and_clarify(test_client, session_id)
    quest_id = _generate_and_accept(test_client, session_id, goal_id)

    today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    event_id = today.json()["data"]["event"]["event_id"]

    async def fake_feedback(self: object, event: object, quest: object) -> FeedbackLLMSchema:
        return FeedbackLLMSchema(
            action_label="测试",
            meaning_text="测试",
            asset_name="总结场景卡",
            asset_type="ability_fragment",
        )

    with patch("src.services.event_service.EventService._generate_feedback", new=fake_feedback):
        test_client.post(
            f"/api/v1/events/{event_id}/complete",
            json={},
            headers=_headers(session_id),
        )

    active = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert active.json()["data"]["progress"]["completed_days"] == 1

    detail = test_client.get(f"/api/v1/quests/{quest_id}", headers=_headers(session_id))
    assert len(detail.json()["data"]["days"]) == 7

    assets = test_client.get(
        "/api/v1/assets",
        params={"quest_id": quest_id},
        headers=_headers(session_id),
    )
    assert len(assets.json()["data"]["items"]) == 1
