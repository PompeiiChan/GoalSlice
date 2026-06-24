"""每日任务与完成反馈服务。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core.exceptions import LLMError
from src.core.downgrade_templates import get_downgrade_template, get_static_downgrade_options
from src.core.feedback_templates import get_feedback_template
from src.db.models import DailyEvent, GrowthAsset, Quest
from src.models.event import (
    ApplyDowngradeResponseData,
    CompleteEventResponseData,
    CompleteFeedbackDTO,
    DailyEventDTO,
    DowngradeOptionDTO,
    DowngradeOptionsLLMSchema,
    DowngradeOptionsResponseData,
    FeedbackAssetDTO,
    FeedbackLLMSchema,
    QuestSummaryDTO,
    TodayEventResponseData,
    TomorrowPreviewDTO,
)
from src.repositories.event_repository import EventRepository
from src.services.llm_service import LLMNode, LLMService


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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


class EventService:
    """今日任务与完成反馈。"""

    def __init__(self, session: AsyncSession, llm_service: LLMService | None = None) -> None:
        self.repo = EventRepository(session)
        self.session = session
        self.llm = llm_service or LLMService()

    async def get_today(self, session_id: str) -> TodayEventResponseData:
        quest = await self.repo.get_active_quest(session_id)
        if not quest:
            raise EventNotFoundError("没有进行中的副本或今日任务")

        event = await self.repo.get_today_event(quest.quest_id, quest.current_day)
        if not event:
            raise EventNotFoundError("没有进行中的副本或今日任务")

        completed_days = await self.repo.count_completed_days(quest.quest_id)

        return TodayEventResponseData(
            event=_event_to_dto(event),
            quest_summary=QuestSummaryDTO(
                quest_title=quest.quest_title,
                current_day=quest.current_day,
                total_days=quest.total_days,
                completed_days=completed_days,
            ),
        )

    async def complete_event(
        self,
        session_id: str,
        event_id: str,
        user_output: str | None = None,
    ) -> CompleteEventResponseData:
        event = await self.repo.get_event_for_session(event_id, session_id)
        if not event:
            raise EventNotFoundError("任务不存在")

        quest = await self.repo.get_active_quest(session_id)
        if not quest or quest.quest_id != event.quest_id:
            raise EventNotFoundError("任务不存在")

        if event.status == "completed":
            raise EventConflictError("任务已完成")

        now = datetime.now(UTC)
        event.user_output = user_output
        event.status = "completed"
        event.completed_at = now
        await self.repo.save_event(event)

        feedback_meta = await self._generate_feedback(event, quest)
        asset_id = str(uuid.uuid4())
        await self.repo.add_growth_asset(
            GrowthAsset(
                asset_id=asset_id,
                session_id=session_id,
                quest_id=quest.quest_id,
                event_id=event.event_id,
                asset_type=feedback_meta.asset_type,
                asset_name=feedback_meta.asset_name,
                asset_content=None,
                created_at=now,
            )
        )

        completed_days = await self.repo.count_completed_days(quest.quest_id)
        is_quest_completed = event.day_index >= quest.total_days

        if not is_quest_completed:
            next_day = event.day_index + 1
            quest.current_day = next_day
            quest.updated_at = now
            next_event = await self.repo.get_event_by_day(quest.quest_id, next_day)
            if next_event and next_event.status == "pending":
                next_event.status = "in_progress"
                await self.repo.save_event(next_event)
        else:
            quest.updated_at = now

        await self.repo.save_quest(quest)
        await self.session.commit()
        await self.session.refresh(event)

        next_preview_day = min(event.day_index + 1, quest.total_days)
        next_event = await self.repo.get_event_by_day(quest.quest_id, next_preview_day)
        tomorrow_title = (
            next_event.event_title
            if next_event and not is_quest_completed
            else "周复盘"
        )

        feedback = CompleteFeedbackDTO(
            completion_title=f"Day {event.day_index} 已完成",
            action_label=feedback_meta.action_label,
            meaning_text=feedback_meta.meaning_text,
            asset=FeedbackAssetDTO(
                asset_id=asset_id,
                asset_type=feedback_meta.asset_type,
                asset_name=feedback_meta.asset_name,
            ),
            progress={
                "completed_days": completed_days,
                "total_days": quest.total_days,
            },
            tomorrow_preview=TomorrowPreviewDTO(
                day_index=next_preview_day,
                event_title=tomorrow_title,
            ),
            is_quest_completed=is_quest_completed,
        )

        return CompleteEventResponseData(event=_event_to_dto(event), feedback=feedback)

    async def request_downgrade(
        self,
        session_id: str,
        event_id: str,
        reason: str | None = None,
    ) -> DowngradeOptionsResponseData:
        event = await self._require_active_event(session_id, event_id)
        options = await self._generate_downgrade_options(event, reason)
        return DowngradeOptionsResponseData(options=options)

    async def apply_downgrade(
        self,
        session_id: str,
        event_id: str,
        option_id: str,
    ) -> ApplyDowngradeResponseData:
        event = await self._require_active_event(session_id, event_id)
        template = get_downgrade_template(option_id)
        if not template:
            raise EventBadRequestError("无效的降级方案")

        if option_id == "tomorrow":
            return ApplyDowngradeResponseData(event=_event_to_dto(event))

        event.status = "downgraded"
        await self.repo.save_event(event)

        new_event = DailyEvent(
            event_id=str(uuid.uuid4()),
            quest_id=event.quest_id,
            day_index=event.day_index,
            event_title=template["event_title"],
            event_description=template["event_description"],
            estimated_time=template["estimated_time"],
            meaning=template["meaning"],
            output_type=template["output_type"],
            output_hint=None,
            user_output=None,
            status="in_progress",
            original_event_id=event.event_id,
            completed_at=None,
        )
        await self.repo.add_event(new_event)
        await self.session.commit()
        await self.session.refresh(new_event)
        return ApplyDowngradeResponseData(event=_event_to_dto(new_event))

    async def _require_active_event(self, session_id: str, event_id: str) -> DailyEvent:
        event = await self.repo.get_event_for_session(event_id, session_id)
        if not event:
            raise EventNotFoundError("任务不存在")
        if event.status != "in_progress":
            raise EventConflictError("当前任务不可降级")
        return event

    async def _generate_downgrade_options(
        self,
        event: DailyEvent,
        reason: str | None,
    ) -> list[DowngradeOptionDTO]:
        static = get_static_downgrade_options()
        messages = [
            {
                "role": "system",
                "content": (
                    "你是职业成长教练，为用户生成 3 个更小的任务降级方案。"
                    "必须包含 option_id 分别为 5min、step1、tomorrow 的三项。"
                    "输出 JSON：options 数组，每项含 option_id, title, description, estimated_time。"
                    "方案须降低时长与认知负担，保留核心价值。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"原任务：{event.event_title}\n"
                    f"说明：{event.event_description}\n"
                    f"用户原因：{reason or '今天太难了'}"
                ),
            },
        ]
        try:
            result = await self.llm.chat_json(
                LLMNode.EVENT_DOWNGRADE,
                messages,
                DowngradeOptionsLLMSchema,
                temperature=0.7,
            )
            if isinstance(result, DowngradeOptionsLLMSchema):
                return result.options
            return DowngradeOptionsLLMSchema.model_validate(result).options
        except LLMError:
            return [DowngradeOptionDTO.model_validate(opt) for opt in static]

    async def _generate_feedback(self, event: DailyEvent, quest: Quest) -> FeedbackLLMSchema:
        template = get_feedback_template(event.day_index)
        messages = [
            {
                "role": "system",
                "content": (
                    "你是职业成长教练，为用户刚完成的任务生成简短意义反馈。"
                    "输出 JSON：action_label, meaning_text（2-4句中文）, "
                    "asset_name, asset_type（template_fragment|ability_fragment|case_note）。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"主线：{quest.quest_title}\n"
                    f"Day {event.day_index} 任务：{event.event_title}\n"
                    f"说明：{event.event_description}\n"
                    f"用户产出：{event.user_output or '（未填写）'}"
                ),
            },
        ]
        try:
            result = await self.llm.chat_json(
                LLMNode.EVENT_COMPLETE,
                messages,
                FeedbackLLMSchema,
                temperature=0.7,
            )
            if isinstance(result, FeedbackLLMSchema):
                return result
            return FeedbackLLMSchema.model_validate(result)
        except LLMError:
            return FeedbackLLMSchema(
                action_label=template["action_label"],
                meaning_text=template["meaning_text"],
                asset_name=template["asset_name"],
                asset_type=template["asset_type"],
            )


class EventNotFoundError(Exception):
    """任务或副本不存在（404）。"""


class EventConflictError(Exception):
    """任务状态冲突（422）。"""


class EventBadRequestError(Exception):
    """请求参数无效（400）。"""
