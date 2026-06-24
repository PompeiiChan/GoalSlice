"""GoalSlice 数据模型 — 基于 pycore 模板扩展。"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


class Goal(Base):
    """目标表。"""

    __tablename__ = "goals"

    goal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    raw_goal: Mapped[str] = mapped_column(Text, nullable=False)
    goal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    refined_goal: Mapped[str] = mapped_column(Text, nullable=False)
    weekly_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    preview_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserContext(Base):
    """用户上下文表（澄清答案）。"""

    __tablename__ = "user_contexts"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    goal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    weekly_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    available_time: Mapped[str] = mapped_column(String(16), nullable=False)
    current_level: Mapped[str] = mapped_column(Text, nullable=False)
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_intensity: Mapped[str] = mapped_column(String(16), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarify_answers_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Quest(Base):
    """7 天计划表。"""

    __tablename__ = "quests"

    quest_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    goal_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quest_title: Mapped[str] = mapped_column(Text, nullable=False)
    success_condition: Mapped[str] = mapped_column(Text, nullable=False)
    total_days: Mapped[int] = mapped_column(nullable=False, default=7, server_default="7")
    current_day: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="in_progress", server_default="in_progress"
    )
    review_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DailyEvent(Base):
    """每日任务表。"""

    __tablename__ = "daily_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quest_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    day_index: Mapped[int] = mapped_column(nullable=False)
    event_title: Mapped[str] = mapped_column(Text, nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_time: Mapped[str] = mapped_column(String(32), nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    output_type: Mapped[str] = mapped_column(String(16), nullable=False)
    output_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", server_default="pending"
    )
    original_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class GrowthAsset(Base):
    """成长资产表。"""

    __tablename__ = "growth_assets"

    asset_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    quest_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
