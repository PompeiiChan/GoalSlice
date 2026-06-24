"""Goal 相关 Pydantic 模型 — 对齐 api-contracts.md。"""

from pydantic import BaseModel, Field


class CreateGoalRequest(BaseModel):
    raw_goal: str = Field(..., max_length=500)


class ClarifyAnswersRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class GoalDTO(BaseModel):
    goal_id: str
    session_id: str
    raw_goal: str
    goal_type: str | None
    refined_goal: str | None
    weekly_outcome: str | None
    status: str
    created_at: str
    updated_at: str


class ClarifyQuestionDTO(BaseModel):
    question_id: str
    question: str
    options: list[str]


class UserContextDTO(BaseModel):
    session_id: str
    goal_type: str
    weekly_outcome: str
    available_time: str
    current_level: str
    failure_reason: str
    preferred_intensity: str
    notes: str


class CreateGoalResponseData(BaseModel):
    goal: GoalDTO
    clarify_questions: list[ClarifyQuestionDTO]


class ClarifyGoalResponseData(BaseModel):
    goal: GoalDTO
    context: UserContextDTO


class ActiveGoalResponseData(BaseModel):
    goal: GoalDTO
    clarify_questions: list[ClarifyQuestionDTO]
    saved_answers: dict[str, str] = Field(default_factory=dict)
    context: UserContextDTO | None = None
