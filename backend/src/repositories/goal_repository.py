"""Goal 数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Goal, Quest, UserContext


class GoalRepository:
    """Goal / UserContext / Quest 查询与写入。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_goal_by_session(self, session_id: str) -> Goal | None:
        result = await self.session.execute(
            select(Goal)
            .where(Goal.session_id == session_id, Goal.status == "active")
            .order_by(Goal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_goal_by_id(self, goal_id: str, session_id: str) -> Goal | None:
        result = await self.session.execute(
            select(Goal).where(Goal.goal_id == goal_id, Goal.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def has_in_progress_quest(self, goal_id: str) -> bool:
        result = await self.session.execute(
            select(Quest.quest_id).where(
                Quest.goal_id == goal_id,
                Quest.status == "in_progress",
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_context(self, session_id: str) -> UserContext | None:
        result = await self.session.execute(
            select(UserContext).where(UserContext.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def add_goal(self, goal: Goal) -> Goal:
        self.session.add(goal)
        await self.session.flush()
        return goal

    async def save_user_context(self, context: UserContext) -> UserContext:
        existing = await self.get_user_context(context.session_id)
        if existing is None:
            self.session.add(context)
            await self.session.flush()
            return context

        existing.goal_type = context.goal_type
        existing.weekly_outcome = context.weekly_outcome
        existing.available_time = context.available_time
        existing.current_level = context.current_level
        existing.failure_reason = context.failure_reason
        existing.preferred_intensity = context.preferred_intensity
        existing.notes = context.notes
        existing.clarify_answers_json = context.clarify_answers_json
        await self.session.flush()
        return existing

    async def update_goal_preview(self, goal_id: str, preview_json: str) -> None:
        goal = await self.session.get(Goal, goal_id)
        if goal is not None:
            goal.preview_json = preview_json
            await self.session.flush()

    async def update_goal_status(self, goal_id: str, status: str) -> None:
        goal = await self.session.get(Goal, goal_id)
        if goal is not None:
            goal.status = status
            await self.session.flush()

    async def clear_goal_preview(self, goal_id: str) -> None:
        goal = await self.session.get(Goal, goal_id)
        if goal is not None:
            goal.preview_json = None
            await self.session.flush()
