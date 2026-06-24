"""Quest 相关 Pydantic 模型 — 对齐 api-contracts.md。"""

from pydantic import BaseModel, Field


class QuestPreviewDayDTO(BaseModel):
    day_index: int
    event_title: str
    event_description: str
    estimated_time: str
    meaning: str
    output_type: str = "text"
    is_boss: bool = False


class QuestPreviewDTO(BaseModel):
    quest_title: str
    success_condition: str
    total_estimated_time: str
    days: list[QuestPreviewDayDTO]


class GenerateQuestRequest(BaseModel):
    goal_id: str


class GenerateQuestResponseData(BaseModel):
    preview: QuestPreviewDTO


class AcceptQuestPreviewInput(BaseModel):
    quest_title: str
    success_condition: str
    days: list[QuestPreviewDayDTO] = Field(default_factory=list)


class AcceptQuestRequest(BaseModel):
    goal_id: str
    preview: AcceptQuestPreviewInput | None = None


class QuestDTO(BaseModel):
    quest_id: str
    goal_id: str
    quest_title: str
    success_condition: str
    total_days: int
    current_day: int
    status: str
    created_at: str
    updated_at: str


class DailyEventDTO(BaseModel):
    event_id: str
    quest_id: str
    day_index: int
    event_title: str
    event_description: str
    estimated_time: str
    meaning: str
    output_type: str
    user_output: str | None
    status: str
    original_event_id: str | None
    completed_at: str | None


class AcceptQuestResponseData(BaseModel):
    quest: QuestDTO
    today_event: DailyEventDTO


class QuestProgressDTO(BaseModel):
    completed_days: int
    total_days: int


class ActiveQuestResponseData(BaseModel):
    quest: QuestDTO
    progress: QuestProgressDTO
    assets_count: int


class QuestDaySummaryDTO(BaseModel):
    day_index: int
    event_title: str
    estimated_time: str
    status: str
    is_boss: bool


class QuestDetailResponseData(BaseModel):
    quest: QuestDTO
    days: list[QuestDaySummaryDTO]


class ReviewAssetDTO(BaseModel):
    asset_id: str
    asset_type: str
    asset_name: str


class NextWeekSuggestionDTO(BaseModel):
    quest_title: str
    description: str


class ReviewDataDTO(BaseModel):
    completed_count: int
    total_days: int
    outputs: list[str]
    assets: list[ReviewAssetDTO]
    observations: list[str]
    boss_summary: str
    next_week_suggestion: NextWeekSuggestionDTO


class ReviewQuestSummaryDTO(BaseModel):
    quest_id: str
    status: str
    current_day: int


class ReviewResponseData(BaseModel):
    review: ReviewDataDTO
    quest: ReviewQuestSummaryDTO


class ReviewLLMSchema(BaseModel):
    outputs: list[str]
    observations: list[str]
    boss_summary: str
    next_week_suggestion: NextWeekSuggestionDTO


class NextWeekRequest(BaseModel):
    accept_suggestion: bool = True


class NextWeekResponseData(BaseModel):
    goal_id: str
    redirect: str
    message: str


class PauseQuestResponseData(BaseModel):
    quest_id: str
    status: str


class QuestPreviewLLMSchema(BaseModel):
    """LLM 结构化输出 Schema。"""

    quest_title: str
    success_condition: str
    total_estimated_time: str
    days: list[QuestPreviewDayDTO]
