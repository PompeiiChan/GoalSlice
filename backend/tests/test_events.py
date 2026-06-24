"""Event API 测试。"""

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
from src.db.models import Base, GrowthAsset, Quest
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


def _seed_accepted_quest(test_client: TestClient, session_id: str) -> tuple[str, str]:
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
    event_id = str(accept.json()["data"]["today_event"]["event_id"])
    return goal_id, event_id


def test_get_today_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "event-today-ok"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["event"]["event_id"] == event_id
    assert body["event"]["day_index"] == 1
    assert body["quest_summary"]["quest_title"]
    assert body["quest_summary"]["completed_days"] == 0


def test_get_today_not_found(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    response = test_client.get("/api/v1/events/today", headers=_headers("empty-session"))
    assert response.status_code == 404


def test_complete_event_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "event-complete-ok"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.post(
        f"/api/v1/events/{event_id}/complete",
        json={"user_output": "背景：周会同步项目进度"},
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["event"]["status"] == "completed"
    assert body["feedback"]["meaning_text"]
    assert body["feedback"]["asset"]["asset_name"]
    assert body["feedback"]["progress"]["completed_days"] == 1
    assert body["feedback"]["tomorrow_preview"]["day_index"] == 2

    today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    assert today.status_code == 200
    assert today.json()["data"]["event"]["day_index"] == 2

    async def verify_db() -> tuple[int, int]:
        async with session_maker() as session:
            assets = await session.execute(select(GrowthAsset))
            quests = await session.execute(select(Quest).where(Quest.status == "in_progress"))
            quest = quests.scalar_one()
            return len(list(assets.scalars().all())), quest.current_day

    asset_count, current_day = asyncio.run(verify_db())
    assert asset_count == 1
    assert current_day == 2


def test_complete_event_uses_llm_fallback(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "event-fallback"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.post(
        f"/api/v1/events/{event_id}/complete",
        json={},
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    assert "总结" in response.json()["data"]["feedback"]["asset"]["asset_name"] or response.json()["data"]["feedback"]["meaning_text"]


def test_complete_event_with_mock_llm(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "event-llm-mock"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    async def fake_feedback(self: object, event: object, quest: object) -> FeedbackLLMSchema:
        return FeedbackLLMSchema(
            action_label="测试动作",
            meaning_text="这是 LLM 生成的意义反馈文案，用于验证结构化输出。",
            asset_name="测试资产",
            asset_type="ability_fragment",
        )

    with patch("src.services.event_service.EventService._generate_feedback", new=fake_feedback):
        response = test_client.post(
            f"/api/v1/events/{event_id}/complete",
            json={},
            headers=_headers(session_id),
        )
    assert response.status_code == 200
    assert response.json()["data"]["feedback"]["meaning_text"].startswith("这是 LLM")


def test_downgrade_options_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "downgrade-options"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.post(
        f"/api/v1/events/{event_id}/downgrade",
        json={"reason": "今天太难了"},
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    options = response.json()["data"]["options"]
    assert len(options) == 3
    assert {opt["option_id"] for opt in options} == {"5min", "step1", "tomorrow"}


def test_apply_downgrade_replaces_event(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "apply-downgrade"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.patch(
        f"/api/v1/events/{event_id}/apply-downgrade",
        json={"option_id": "5min"},
        headers=_headers(session_id),
    )
    assert response.status_code == 200
    body = response.json()["data"]["event"]
    assert body["status"] == "in_progress"
    assert body["original_event_id"] == event_id
    assert "5 分钟版" in body["event_title"]
    assert body["output_type"] == "checkbox"

    today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    assert today.status_code == 200
    assert today.json()["data"]["event"]["event_id"] == body["event_id"]

    async def verify_original() -> str | None:
        async with session_maker() as session:
            from src.db.models import DailyEvent

            result = await session.execute(
                select(DailyEvent).where(DailyEvent.event_id == event_id)
            )
            original = result.scalar_one()
            return original.status

    assert asyncio.run(verify_original()) == "downgraded"


def test_apply_downgrade_invalid_option(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "downgrade-invalid"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    response = test_client.patch(
        f"/api/v1/events/{event_id}/apply-downgrade",
        json={"option_id": "invalid"},
        headers=_headers(session_id),
    )
    assert response.status_code == 400


def test_downgraded_complete_advances_day(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "downgrade-complete"
    _, event_id = _seed_accepted_quest(test_client, session_id)

    applied = test_client.patch(
        f"/api/v1/events/{event_id}/apply-downgrade",
        json={"option_id": "5min"},
        headers=_headers(session_id),
    )
    new_event_id = applied.json()["data"]["event"]["event_id"]

    complete = test_client.post(
        f"/api/v1/events/{new_event_id}/complete",
        json={},
        headers=_headers(session_id),
    )
    assert complete.status_code == 200
    assert complete.json()["data"]["feedback"]["progress"]["completed_days"] == 1

    today = test_client.get("/api/v1/events/today", headers=_headers(session_id))
    assert today.json()["data"]["event"]["day_index"] == 2

