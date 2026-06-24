"""Quest API 测试（隔离测试库 + Mock LLM）。"""

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
from src.db.models import Base, DailyEvent
from src.main import app

SESSION_HEADER = "X-Session-Id"
CLARIFY_ANSWERS = {
    "goal_type": "技能提升",
    "weekly_outcome": "完成一个具体产物",
    "available_time": "15 分钟",
    "current_level": "有一点了解，但不系统",
    "failure_reason": "不知道第一步做什么",
}
OTHER_CLARIFY_ANSWERS = {**CLARIFY_ANSWERS, "goal_type": "其他"}


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


def _create_and_clarify(
    test_client: TestClient,
    session_id: str,
    raw_goal: str = "我想提升自己的会议总结能力",
    answers: dict[str, str] | None = None,
) -> str:
    create = test_client.post(
        "/api/v1/goals",
        json={"raw_goal": raw_goal},
        headers=_headers(session_id),
    )
    assert create.status_code == 200
    goal_id = str(create.json()["data"]["goal"]["goal_id"])
    clarify = test_client.patch(
        f"/api/v1/goals/{goal_id}/clarify",
        json={"answers": answers or CLARIFY_ANSWERS},
        headers=_headers(session_id),
    )
    assert clarify.status_code == 200
    return goal_id


def test_generate_quest_success(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-generate-ok"
    goal_id = _create_and_clarify(test_client, session_id)

    async def fake_llm(self: object, goal: object, context: object) -> object:
        return build_meeting_summary_preview()

    with patch(
        "src.services.quest_service.QuestService._generate_with_llm",
        new=fake_llm,
    ):
        response = test_client.post(
            "/api/v1/quests/generate",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    preview = body["data"]["preview"]
    assert preview["quest_title"]
    assert len(preview["days"]) == 7
    assert preview["days"][6]["is_boss"] is True


def test_generate_quest_out_of_scope(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-out-scope"
    goal_id = _create_and_clarify(
        test_client,
        session_id,
        raw_goal="我想学做饭",
        answers=OTHER_CLARIFY_ANSWERS,
    )

    response = test_client.post(
        "/api/v1/quests/generate",
        json={"goal_id": goal_id},
        headers=_headers(session_id),
    )
    assert response.status_code == 422
    assert "MVP" in response.json()["message"]


def test_generate_quest_llm_unavailable(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-llm-503"
    goal_id = _create_and_clarify(test_client, session_id)

    response = test_client.post(
        "/api/v1/quests/generate",
        json={"goal_id": goal_id},
        headers=_headers(session_id),
    )
    assert response.status_code == 503
    assert "AI 服务" in response.json()["message"]


def test_accept_quest_persists_quest_and_events(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, session_maker = client
    session_id = "quest-accept-ok"
    goal_id = _create_and_clarify(test_client, session_id)
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
            json={
                "goal_id": goal_id,
                "preview": {
                    "quest_title": preview.quest_title,
                    "success_condition": preview.success_condition,
                    "days": [d.model_dump() for d in preview.days],
                },
            },
            headers=_headers(session_id),
        )

    assert accept.status_code == 200
    data = accept.json()["data"]
    assert data["quest"]["status"] == "in_progress"
    assert data["today_event"]["day_index"] == 1
    assert data["today_event"]["status"] == "in_progress"

    quest_id = data["quest"]["quest_id"]

    async def count_events() -> int:
        async with session_maker() as session:
            result = await session.execute(
                select(DailyEvent).where(DailyEvent.quest_id == quest_id)
            )
            return len(list(result.scalars().all()))

    assert asyncio.run(count_events()) == 7


def test_accept_quest_conflict_when_already_in_progress(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-accept-conflict"
    goal_id = _create_and_clarify(test_client, session_id)
    preview = build_meeting_summary_preview()

    async def fake_llm(self: object, goal: object, context: object) -> object:
        return preview

    with patch("src.services.quest_service.QuestService._generate_with_llm", new=fake_llm):
        test_client.post(
            "/api/v1/quests/generate",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
        first = test_client.post(
            "/api/v1/quests",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
        assert first.status_code == 200

        second = test_client.post(
            "/api/v1/quests",
            json={"goal_id": goal_id},
            headers=_headers(session_id),
        )
    assert second.status_code == 422


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
    assert accept.status_code == 200
    return str(accept.json()["data"]["quest"]["quest_id"])


def test_get_active_quest_with_progress(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-active-ok"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)

    response = test_client.get("/api/v1/quests/active", headers=_headers(session_id))
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["data"]["quest"]["quest_id"] == quest_id
    assert body["data"]["progress"]["completed_days"] == 0
    assert body["data"]["assets_count"] == 0


def test_get_active_quest_null_when_none(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    response = test_client.get("/api/v1/quests/active", headers=_headers("empty-session"))
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_get_quest_detail(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    session_id = "quest-detail-ok"
    goal_id = _create_and_clarify(test_client, session_id)
    quest_id = _accept_quest(test_client, session_id, goal_id)

    response = test_client.get(f"/api/v1/quests/{quest_id}", headers=_headers(session_id))
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["days"]) == 7
    assert data["days"][0]["status"] == "pending"
    assert data["days"][6]["is_boss"] is True


def test_get_quest_detail_not_found(
    client: tuple[TestClient, AsyncEngine, async_sessionmaker[AsyncSession]],
) -> None:
    test_client, _, _ = client
    response = test_client.get(
        "/api/v1/quests/nonexistent-quest-id",
        headers=_headers("no-quest-session"),
    )
    assert response.status_code == 404
