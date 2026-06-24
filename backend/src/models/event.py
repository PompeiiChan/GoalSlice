"""Event API Pydantic 模型 — 对齐 api-contracts.md。"""

from pydantic import BaseModel, Field


class DailyEventDTO(BaseModel):
    event_id: str
    quest_id: str
    day_index: int
    event_title: str
    event_description: str
    estimated_time: str
    meaning: str
    output_type: str
    user_output: str | None = None
    status: str
    original_event_id: str | None = None
    completed_at: str | None = None


class QuestSummaryDTO(BaseModel):
    quest_title: str
    current_day: int
    total_days: int
    completed_days: int = 0


class TodayEventResponseData(BaseModel):
    event: DailyEventDTO
    quest_summary: QuestSummaryDTO


class CompleteEventRequest(BaseModel):
    user_output: str | None = None


class FeedbackAssetDTO(BaseModel):
    asset_id: str
    asset_type: str
    asset_name: str


class TomorrowPreviewDTO(BaseModel):
    day_index: int
    event_title: str


class CompleteFeedbackDTO(BaseModel):
    completion_title: str
    action_label: str
    meaning_text: str
    asset: FeedbackAssetDTO
    progress: dict[str, int]
    tomorrow_preview: TomorrowPreviewDTO
    is_quest_completed: bool


class CompleteEventResponseData(BaseModel):
    event: DailyEventDTO
    feedback: CompleteFeedbackDTO


class FeedbackLLMSchema(BaseModel):
    action_label: str
    meaning_text: str
    asset_name: str
    asset_type: str = Field(pattern="^(template_fragment|ability_fragment|case_note)$")


class DowngradeRequest(BaseModel):
    reason: str | None = None


class DowngradeOptionDTO(BaseModel):
    option_id: str
    title: str
    description: str
    estimated_time: str


class DowngradeOptionsResponseData(BaseModel):
    options: list[DowngradeOptionDTO]


class DowngradeOptionsLLMSchema(BaseModel):
    options: list[DowngradeOptionDTO]


class ApplyDowngradeRequest(BaseModel):
    option_id: str


class ApplyDowngradeResponseData(BaseModel):
    event: DailyEventDTO
