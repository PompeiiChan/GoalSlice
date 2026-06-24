"""Quest 计划生成与接受服务。"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core.exceptions import LLMError
from src.core.quest_templates import (
    DAILY_EVENT_TITLE_OVERRIDE,
    MVP_GOAL_TYPES,
    OUT_OF_SCOPE_MESSAGE,
    build_quest_generate_prompt,
)
from src.core.review_templates import build_static_review
from src.db.models import DailyEvent, Goal, Quest, UserContext
from src.models.quest import (
    AcceptQuestResponseData,
    ActiveQuestResponseData,
    DailyEventDTO,
    GenerateQuestResponseData,
    NextWeekResponseData,
    PauseQuestResponseData,
    QuestDaySummaryDTO,
    QuestDetailResponseData,
    QuestDTO,
    QuestPreviewDTO,
    QuestPreviewLLMSchema,
    QuestProgressDTO,
    ReviewAssetDTO,
    ReviewDataDTO,
    ReviewLLMSchema,
    ReviewQuestSummaryDTO,
    ReviewResponseData,
)
from src.repositories.asset_repository import AssetRepository
from src.repositories.event_repository import EventRepository
from src.repositories.goal_repository import GoalRepository
from src.repositories.quest_repository import QuestRepository
from src.services.goal_service import GoalConflictError, GoalNotFoundError
from src.services.llm_service import LLMNode, LLMService


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _quest_to_dto(quest: Quest) -> QuestDTO:
    return QuestDTO(
        quest_id=quest.quest_id,
        goal_id=quest.goal_id,
        quest_title=quest.quest_title,
        success_condition=quest.success_condition,
        total_days=quest.total_days,
        current_day=quest.current_day,
        status=quest.status,
        created_at=_iso_z(quest.created_at),
        updated_at=_iso_z(quest.updated_at),
    )


def _event_to_dto(event: DailyEvent) -> DailyEventDTO:
    return DailyEventDTO(
        event_id=event.event_id,
        quest_id=event.quest_id,
        day_index=event.day_index,
        event_title=event.event_title,
        event_description=event.event_description,
        estimated_time=event.estimated_time,
        meaning=event.meaning,
        output_type=event.output_type,
        user_output=event.user_output,
        status=event.status,
        original_event_id=event.original_event_id,
        completed_at=_iso_z(event.completed_at) if event.completed_at else None,
    )


def _validate_preview(preview: QuestPreviewDTO) -> None:
    if len(preview.days) != 7:
        raise ValueError("计划须包含 7 天任务")
    indices = sorted(day.day_index for day in preview.days)
    if indices != list(range(1, 8)):
        raise ValueError("day_index 须为 1-7")
    if not any(day.is_boss for day in preview.days if day.day_index == 7):
        raise ValueError("第 7 天须标记为 Boss")


class QuestService:
    """计划生成与副本创建。"""

    def __init__(self, session: AsyncSession, llm_service: LLMService | None = None) -> None:
        self.goal_repo = GoalRepository(session)
        self.quest_repo = QuestRepository(session)
        self.event_repo = EventRepository(session)
        self.asset_repo = AssetRepository(session)
        self.session = session
        self.llm = llm_service or LLMService()

    async def generate_preview(
        self, session_id: str, goal_id: str
    ) -> GenerateQuestResponseData:
        goal = await self.goal_repo.get_goal_by_id(goal_id, session_id)
        if not goal:
            raise GoalNotFoundError("目标不存在")

        if not goal.refined_goal:
            raise ValueNotFoundError("请先完成澄清再生成计划")

        if goal.goal_type not in MVP_GOAL_TYPES:
            raise QuestOutOfScopeError(OUT_OF_SCOPE_MESSAGE)

        context = await self.goal_repo.get_user_context(session_id)
        if not context or not context.weekly_outcome:
            raise ValueNotFoundError("请先完成澄清再生成计划")

        preview = await self._generate_with_llm(goal, context)
        _validate_preview(preview)

        await self.goal_repo.update_goal_preview(
            goal_id, json.dumps(preview.model_dump(), ensure_ascii=False)
        )
        await self.session.commit()

        return GenerateQuestResponseData(preview=preview)

    async def accept_quest(
        self,
        session_id: str,
        goal_id: str,
        preview_input: QuestPreviewDTO | None = None,
    ) -> AcceptQuestResponseData:
        goal = await self.goal_repo.get_goal_by_id(goal_id, session_id)
        if not goal:
            raise GoalNotFoundError("目标不存在")

        if await self.quest_repo.has_in_progress_quest_for_session(session_id):
            raise GoalConflictError("已有进行中的副本，请先完成或暂停")

        preview = preview_input or self._load_stored_preview(goal.preview_json)
        if preview is None:
            raise ValueNotFoundError("请先生成计划预览")

        _validate_preview(preview)

        now = datetime.now(UTC)
        quest_id = str(uuid.uuid4())
        quest = Quest(
            quest_id=quest_id,
            goal_id=goal_id,
            quest_title=preview.quest_title,
            success_condition=preview.success_condition,
            total_days=7,
            current_day=1,
            status="in_progress",
            created_at=now,
            updated_at=now,
        )
        await self.quest_repo.add_quest(quest)

        events: list[DailyEvent] = []
        for day in sorted(preview.days, key=lambda d: d.day_index):
            title = DAILY_EVENT_TITLE_OVERRIDE.get(day.day_index, day.event_title)
            events.append(
                DailyEvent(
                    event_id=str(uuid.uuid4()),
                    quest_id=quest_id,
                    day_index=day.day_index,
                    event_title=title,
                    event_description=day.event_description,
                    estimated_time=day.estimated_time,
                    meaning=day.meaning,
                    output_type=day.output_type,
                    output_hint=None,
                    user_output=None,
                    status="in_progress" if day.day_index == 1 else "pending",
                    original_event_id=None,
                    completed_at=None,
                )
            )

        await self.quest_repo.add_events(events)
        await self.session.commit()
        await self.session.refresh(quest)

        today_event = next(e for e in events if e.day_index == 1)
        return AcceptQuestResponseData(
            quest=_quest_to_dto(quest),
            today_event=_event_to_dto(today_event),
        )

    async def get_active_quest(self, session_id: str) -> ActiveQuestResponseData | None:
        quest = await self.quest_repo.get_active_quest(session_id)
        if not quest:
            return None

        completed_days = await self.event_repo.count_completed_days(quest.quest_id)
        assets_count = await self.asset_repo.count_assets(session_id, quest.quest_id)

        return ActiveQuestResponseData(
            quest=_quest_to_dto(quest),
            progress=QuestProgressDTO(
                completed_days=completed_days,
                total_days=quest.total_days,
            ),
            assets_count=assets_count,
        )

    async def get_quest_detail(
        self, session_id: str, quest_id: str
    ) -> QuestDetailResponseData:
        quest = await self.quest_repo.get_quest_for_session(quest_id, session_id)
        if not quest:
            raise QuestNotFoundError("副本不存在")

        events = await self.quest_repo.get_events_by_quest(quest_id)
        days = _build_quest_day_summaries(events)

        return QuestDetailResponseData(quest=_quest_to_dto(quest), days=days)

    async def generate_review(self, session_id: str, quest_id: str) -> ReviewResponseData:
        quest = await self.quest_repo.get_quest_for_session(quest_id, session_id)
        if not quest:
            raise QuestNotFoundError("副本不存在")

        if quest.review_json:
            review = ReviewDataDTO.model_validate(json.loads(quest.review_json))
            return ReviewResponseData(
                review=review,
                quest=ReviewQuestSummaryDTO(
                    quest_id=quest.quest_id,
                    status=quest.status,
                    current_day=quest.current_day,
                ),
            )

        if quest.status != "in_progress" or quest.current_day != 7:
            raise QuestConflictError("尚未完成本周副本，无法复盘")

        events = await self.quest_repo.get_events_by_quest(quest_id)
        day7 = _primary_event_for_day(events, 7)
        if not day7 or day7.status != "completed":
            raise QuestConflictError("尚未完成本周副本，无法复盘")

        completed_count = await self.event_repo.count_completed_days(quest_id)
        outputs = [
            e.event_title
            for e in sorted(events, key=lambda item: item.day_index)
            if e.status == "completed"
        ]
        assets = await self.asset_repo.list_assets(session_id, quest_id)
        review_assets = [
            ReviewAssetDTO(
                asset_id=a.asset_id,
                asset_type=a.asset_type,
                asset_name=a.asset_name,
            )
            for a in assets
        ]

        review = await self._generate_review(quest, outputs, review_assets, completed_count)

        now = datetime.now(UTC)
        quest.status = "completed"
        quest.updated_at = now
        quest.review_json = json.dumps(review.model_dump(), ensure_ascii=False)
        await self.quest_repo.save_quest(quest)
        await self.session.commit()

        return ReviewResponseData(
            review=review,
            quest=ReviewQuestSummaryDTO(
                quest_id=quest.quest_id,
                status=quest.status,
                current_day=quest.current_day,
            ),
        )

    async def start_next_week(
        self,
        session_id: str,
        quest_id: str,
        accept_suggestion: bool,
    ) -> NextWeekResponseData:
        quest = await self.quest_repo.get_quest_for_session(quest_id, session_id)
        if not quest:
            raise QuestNotFoundError("副本不存在")
        if quest.status != "completed":
            raise QuestConflictError("请先完成周复盘")
        if not accept_suggestion:
            raise QuestConflictError("须确认开启下一周")

        goal = await self.goal_repo.get_goal_by_id(quest.goal_id, session_id)
        if not goal:
            raise GoalNotFoundError("目标不存在")

        await self.goal_repo.update_goal_status(quest.goal_id, "active")
        await self.goal_repo.clear_goal_preview(quest.goal_id)
        await self.session.commit()

        return NextWeekResponseData(
            goal_id=goal.goal_id,
            redirect="clarify",
            message="已准备好进入下一周副本",
        )

    async def pause_quest(self, session_id: str, quest_id: str) -> PauseQuestResponseData:
        quest = await self.quest_repo.get_quest_for_session(quest_id, session_id)
        if not quest:
            raise QuestNotFoundError("副本不存在")
        if quest.status == "abandoned":
            raise QuestConflictError("副本已暂停")

        now = datetime.now(UTC)
        quest.status = "abandoned"
        quest.updated_at = now
        await self.goal_repo.update_goal_status(quest.goal_id, "paused")
        await self.quest_repo.save_quest(quest)
        await self.session.commit()

        return PauseQuestResponseData(quest_id=quest_id, status="abandoned")

    async def _generate_review(
        self,
        quest: Quest,
        outputs: list[str],
        assets: list[ReviewAssetDTO],
        completed_count: int,
    ) -> ReviewDataDTO:
        asset_dicts = [a.model_dump() for a in assets]
        messages = [
            {
                "role": "system",
                "content": (
                    "你是职业成长教练，为用户生成本周复盘。"
                    "输出 JSON：outputs（字符串数组）, observations（1-2句中文数组）, "
                    "boss_summary（一句中文）, next_week_suggestion {quest_title, description}。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"主线：{quest.quest_title}\n"
                    f"通关条件：{quest.success_condition}\n"
                    f"完成天数：{completed_count}/7\n"
                    f"任务产出：{'; '.join(outputs)}"
                ),
            },
        ]
        try:
            result = await self.llm.chat_json(
                LLMNode.QUEST_REVIEW,
                messages,
                ReviewLLMSchema,
                temperature=0.7,
            )
            if isinstance(result, ReviewLLMSchema):
                llm_review = result
            else:
                llm_review = ReviewLLMSchema.model_validate(result)
            return ReviewDataDTO(
                completed_count=completed_count,
                total_days=quest.total_days,
                outputs=llm_review.outputs,
                assets=assets,
                observations=llm_review.observations,
                boss_summary=llm_review.boss_summary,
                next_week_suggestion=llm_review.next_week_suggestion,
            )
        except LLMError:
            static = build_static_review(completed_count, outputs, asset_dicts)
            return ReviewDataDTO.model_validate(static)

    async def _generate_with_llm(self, goal: Goal, context: UserContext) -> QuestPreviewDTO:
        messages = build_quest_generate_prompt(
            raw_goal=goal.raw_goal,
            refined_goal=goal.refined_goal,
            weekly_outcome=context.weekly_outcome,
            available_time=context.available_time,
            current_level=context.current_level,
            failure_reason=context.failure_reason,
        )

        try:
            result = await self.llm.chat_json(
                LLMNode.QUEST_GENERATE,
                messages,
                QuestPreviewLLMSchema,
                temperature=0.7,
            )
            if isinstance(result, QuestPreviewLLMSchema):
                return QuestPreviewDTO.model_validate(result.model_dump())
            return QuestPreviewDTO.model_validate(result)
        except LLMError as exc:
            raise LLMUnavailableError(str(exc)) from exc

    @staticmethod
    def _load_stored_preview(preview_json: str | None) -> QuestPreviewDTO | None:
        if not preview_json:
            return None
        try:
            data = json.loads(preview_json)
            preview = QuestPreviewDTO.model_validate(data)
            _validate_preview(preview)
            return preview
        except (json.JSONDecodeError, ValidationError, ValueError):
            return None


def _primary_event_for_day(events: list[DailyEvent], day_index: int) -> DailyEvent | None:
    day_events = [e for e in events if e.day_index == day_index]
    if not day_events:
        return None
    for status in ("in_progress", "completed", "pending", "downgraded"):
        for event in day_events:
            if event.status == status:
                return event
    return day_events[0]


def _build_quest_day_summaries(events: list[DailyEvent]) -> list[QuestDaySummaryDTO]:
    summaries: list[QuestDaySummaryDTO] = []
    for day_index in range(1, 8):
        event = _primary_event_for_day(events, day_index)
        if not event:
            continue
        summaries.append(
            QuestDaySummaryDTO(
                day_index=day_index,
                event_title=event.event_title,
                estimated_time=event.estimated_time,
                status="completed" if event.status == "completed" else "pending",
                is_boss=day_index == 7,
            )
        )
    return summaries


class QuestNotFoundError(Exception):
    """副本不存在（404）。"""


class QuestConflictError(Exception):
    """副本状态冲突（422）。"""


class QuestOutOfScopeError(Exception):
    """非 MVP 目标（422）。"""


class ValueNotFoundError(Exception):
    """前置条件不满足（404）。"""


class LLMUnavailableError(Exception):
    """LLM 不可用（503）。"""
