"""Quest / DailyEvent 数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import DailyEvent, Goal, Quest


class QuestRepository:
    """Quest 与 DailyEvent 查询与写入。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def has_in_progress_quest_for_session(self, session_id: str) -> bool:
        result = await self.session.execute(
            select(Quest.quest_id)
            .join(Goal, Quest.goal_id == Goal.goal_id)
            .where(Goal.session_id == session_id, Quest.status == "in_progress")
        )
        return result.scalar_one_or_none() is not None

    async def add_quest(self, quest: Quest) -> Quest:
        self.session.add(quest)
        await self.session.flush()
        return quest

    async def add_events(self, events: list[DailyEvent]) -> None:
        self.session.add_all(events)
        await self.session.flush()

    async def get_events_by_quest(self, quest_id: str) -> list[DailyEvent]:
        result = await self.session.execute(
            select(DailyEvent)
            .where(DailyEvent.quest_id == quest_id)
            .order_by(DailyEvent.day_index)
        )
        return list(result.scalars().all())

    async def get_active_quest(self, session_id: str) -> Quest | None:
        result = await self.session.execute(
            select(Quest)
            .join(Goal, Quest.goal_id == Goal.goal_id)
            .where(Goal.session_id == session_id, Quest.status == "in_progress")
            .order_by(Quest.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_quest_for_session(self, quest_id: str, session_id: str) -> Quest | None:
        result = await self.session.execute(
            select(Quest)
            .join(Goal, Quest.goal_id == Goal.goal_id)
            .where(Quest.quest_id == quest_id, Goal.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def save_quest(self, quest: Quest) -> Quest:
        await self.session.flush()
        return quest
