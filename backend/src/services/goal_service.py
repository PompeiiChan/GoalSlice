"""Goal 业务逻辑。"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.clarify_data import (
    CLARIFY_QUESTIONS,
    GOAL_TYPE_LABEL_TO_CODE,
    TIME_LABEL_TO_CODE,
)
from src.db.models import Goal, UserContext
from src.models.goal import (
    ActiveGoalResponseData,
    ClarifyGoalResponseData,
    ClarifyQuestionDTO,
    CreateGoalResponseData,
    GoalDTO,
    UserContextDTO,
)
from src.repositories.goal_repository import GoalRepository


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _goal_to_dto(goal: Goal) -> GoalDTO:
    return GoalDTO(
        goal_id=goal.goal_id,
        session_id=goal.session_id,
        raw_goal=goal.raw_goal,
        goal_type=goal.goal_type or None,
        refined_goal=goal.refined_goal or None,
        weekly_outcome=goal.weekly_outcome or None,
        status=goal.status,
        created_at=_iso_z(goal.created_at),
        updated_at=_iso_z(goal.updated_at),
    )


def _context_to_dto(context: UserContext) -> UserContextDTO:
    return UserContextDTO(
        session_id=context.session_id,
        goal_type=context.goal_type,
        weekly_outcome=context.weekly_outcome,
        available_time=context.available_time,
        current_level=context.current_level,
        failure_reason=context.failure_reason,
        preferred_intensity=context.preferred_intensity,
        notes=context.notes or "",
    )


def _clarify_questions_dto() -> list[ClarifyQuestionDTO]:
    return [ClarifyQuestionDTO(**q) for q in CLARIFY_QUESTIONS]


def _infer_refined_goal(raw_goal: str) -> str:
    if "会议总结" in raw_goal:
        return "提升会议总结能力"
    refined = raw_goal.strip()
    if refined.startswith("我想"):
        refined = refined[2:].strip()
    return refined


class GoalService:
    """目标创建与澄清服务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = GoalRepository(session)
        self.session = session

    async def create_goal(self, session_id: str, raw_goal: str) -> CreateGoalResponseData:
        trimmed = raw_goal.strip()
        if not trimmed:
            raise ValueError("raw_goal 不能为空")

        active = await self.repo.get_active_goal_by_session(session_id)
        if active and await self.repo.has_in_progress_quest(active.goal_id):
            raise GoalConflictError("已有进行中的副本，请先完成或暂停")

        now = datetime.now(UTC)
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            session_id=session_id,
            raw_goal=trimmed,
            goal_type="skill_up" if "会议总结" in trimmed else "",
            refined_goal="",
            weekly_outcome="",
            status="active",
            created_at=now,
            updated_at=now,
        )
        await self.repo.add_goal(goal)
        await self.session.commit()
        await self.session.refresh(goal)

        return CreateGoalResponseData(
            goal=_goal_to_dto(goal),
            clarify_questions=_clarify_questions_dto(),
        )

    async def clarify_goal(
        self,
        session_id: str,
        goal_id: str,
        answers: dict[str, str],
        notes: str = "",
    ) -> ClarifyGoalResponseData:
        goal = await self.repo.get_goal_by_id(goal_id, session_id)
        if not goal:
            raise GoalNotFoundError("目标不存在")

        context = await self.repo.get_user_context(session_id)
        saved_answers = self._load_saved_answers(context)
        saved_answers.update({k: v for k, v in answers.items() if v})

        is_complete = all(q["question_id"] in saved_answers for q in CLARIFY_QUESTIONS)

        goal_type_label = saved_answers.get("goal_type", "技能提升")
        goal_type = GOAL_TYPE_LABEL_TO_CODE.get(goal_type_label, "skill_up")
        weekly_outcome = saved_answers.get("weekly_outcome", "完成一个具体产物")
        available_time = TIME_LABEL_TO_CODE.get(
            saved_answers.get("available_time", "15 分钟"), "15m"
        )
        current_level = saved_answers.get("current_level", "有一点了解，但不系统")
        failure_reason = saved_answers.get("failure_reason", "不知道第一步做什么")

        now = datetime.now(UTC)

        if context is None:
            context = UserContext(
                session_id=session_id,
                goal_type=goal_type if is_complete else "",
                weekly_outcome=weekly_outcome if is_complete else "",
                available_time=available_time if is_complete else "",
                current_level=current_level if is_complete else "",
                failure_reason=failure_reason if is_complete else "",
                preferred_intensity="low",
                notes=notes or "",
                clarify_answers_json=json.dumps(saved_answers, ensure_ascii=False),
            )
        else:
            context.clarify_answers_json = json.dumps(saved_answers, ensure_ascii=False)
            if notes:
                context.notes = notes

        if is_complete:
            goal.goal_type = goal_type
            goal.refined_goal = _infer_refined_goal(goal.raw_goal)
            goal.weekly_outcome = weekly_outcome
            goal.updated_at = now
            context.goal_type = goal_type
            context.weekly_outcome = weekly_outcome
            context.available_time = available_time
            context.current_level = current_level
            context.failure_reason = failure_reason
            context.preferred_intensity = "low"

        await self.repo.save_user_context(context)
        await self.session.commit()
        await self.session.refresh(goal)
        refreshed_context = await self.repo.get_user_context(session_id)
        assert refreshed_context is not None

        return ClarifyGoalResponseData(
            goal=_goal_to_dto(goal),
            context=_context_to_dto(refreshed_context),
        )

    async def get_active_goal(self, session_id: str) -> ActiveGoalResponseData | None:
        goal = await self.repo.get_active_goal_by_session(session_id)
        if not goal:
            return None

        context = await self.repo.get_user_context(session_id)
        saved_answers = self._load_saved_answers(context)
        context_dto = _context_to_dto(context) if context and goal.refined_goal else None

        return ActiveGoalResponseData(
            goal=_goal_to_dto(goal),
            clarify_questions=_clarify_questions_dto(),
            saved_answers=saved_answers,
            context=context_dto,
        )

    @staticmethod
    def _load_saved_answers(context: UserContext | None) -> dict[str, str]:
        if not context or not context.clarify_answers_json:
            return {}
        try:
            loaded: dict[str, Any] = json.loads(context.clarify_answers_json)
            return {str(k): str(v) for k, v in loaded.items()}
        except json.JSONDecodeError:
            return {}


class GoalNotFoundError(Exception):
    """目标不存在。"""


class GoalConflictError(Exception):
    """业务冲突（422）。"""
