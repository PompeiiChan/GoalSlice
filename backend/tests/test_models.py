"""测试数据库模型定义。"""

from src.db.models import Base, DailyEvent, Goal, GrowthAsset, Quest, UserContext


def test_base_exists() -> None:
    """Base 类存在。"""
    assert Base is not None


def test_goal_model_has_required_fields() -> None:
    """Goal 模型包含必需字段。"""
    assert hasattr(Goal, "__tablename__")
    assert Goal.__tablename__ == "goals"
    assert hasattr(Goal, "goal_id")
    assert hasattr(Goal, "session_id")
    assert hasattr(Goal, "raw_goal")
    assert hasattr(Goal, "goal_type")
    assert hasattr(Goal, "refined_goal")
    assert hasattr(Goal, "weekly_outcome")
    assert hasattr(Goal, "status")
    assert hasattr(Goal, "created_at")
    assert hasattr(Goal, "updated_at")


def test_user_context_model_has_required_fields() -> None:
    """UserContext 模型包含必需字段。"""
    assert hasattr(UserContext, "__tablename__")
    assert UserContext.__tablename__ == "user_contexts"
    assert hasattr(UserContext, "session_id")
    assert hasattr(UserContext, "goal_type")
    assert hasattr(UserContext, "available_time")


def test_quest_model_has_required_fields() -> None:
    """Quest 模型包含必需字段。"""
    assert hasattr(Quest, "__tablename__")
    assert Quest.__tablename__ == "quests"
    assert hasattr(Quest, "quest_id")
    assert hasattr(Quest, "goal_id")
    assert hasattr(Quest, "total_days")
    assert hasattr(Quest, "current_day")


def test_daily_event_model_has_required_fields() -> None:
    """DailyEvent 模型包含必需字段。"""
    assert hasattr(DailyEvent, "__tablename__")
    assert DailyEvent.__tablename__ == "daily_events"
    assert hasattr(DailyEvent, "event_id")
    assert hasattr(DailyEvent, "quest_id")
    assert hasattr(DailyEvent, "day_index")
    assert hasattr(DailyEvent, "output_type")


def test_growth_asset_model_has_required_fields() -> None:
    """GrowthAsset 模型包含必需字段。"""
    assert hasattr(GrowthAsset, "__tablename__")
    assert GrowthAsset.__tablename__ == "growth_assets"
    assert hasattr(GrowthAsset, "asset_id")
    assert hasattr(GrowthAsset, "session_id")
    assert hasattr(GrowthAsset, "quest_id")
    assert hasattr(GrowthAsset, "asset_type")
