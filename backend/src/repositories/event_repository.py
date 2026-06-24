"""Event / Quest 查询（今日任务、完成反馈）。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import DailyEvent, Goal, GrowthAsset, Quest


class EventRepository:
    """DailyEvent 与活跃副本查询。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_quest(self, session_id: str) -> Quest | None:
        result = await self.session.execute(
            select(Quest)
            .join(Goal, Quest.goal_id == Goal.goal_id)
            .where(Goal.session_id == session_id, Quest.status == "in_progress")
            .order_by(Quest.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_today_event(self, quest_id: str, current_day: int) -> DailyEvent | None:
        result = await self.session.execute(
            select(DailyEvent).where(
                DailyEvent.quest_id == quest_id,
                DailyEvent.day_index == current_day,
                DailyEvent.status.in_(("in_progress", "pending")),
            )
        )
        event = result.scalar_one_or_none()
        if event is not None:
            return event
        result = await self.session.execute(
            select(DailyEvent).where(
                DailyEvent.quest_id == quest_id,
                DailyEvent.day_index == current_day,
            )
        )
        return result.scalar_one_or_none()

    async def get_event_by_id(self, event_id: str) -> DailyEvent | None:
        result = await self.session.execute(
            select(DailyEvent).where(DailyEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_event_for_session(self, event_id: str, session_id: str) -> DailyEvent | None:
        result = await self.session.execute(
            select(DailyEvent)
            .join(Quest, DailyEvent.quest_id == Quest.quest_id)
            .join(Goal, Quest.goal_id == Goal.goal_id)
            .where(DailyEvent.event_id == event_id, Goal.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def count_completed_days(self, quest_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(DailyEvent)
            .where(DailyEvent.quest_id == quest_id, DailyEvent.status == "completed")
        )
        return int(result.scalar_one() or 0)

    async def get_event_by_day(self, quest_id: str, day_index: int) -> DailyEvent | None:
        result = await self.session.execute(
            select(DailyEvent).where(
                DailyEvent.quest_id == quest_id,
                DailyEvent.day_index == day_index,
            )
        )
        return result.scalar_one_or_none()

    async def add_growth_asset(self, asset: GrowthAsset) -> GrowthAsset:
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def add_event(self, event: DailyEvent) -> DailyEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def save_event(self, event: DailyEvent) -> DailyEvent:
        await self.session.flush()
        return event

    async def save_quest(self, quest: Quest) -> Quest:
        await self.session.flush()
        return quest
