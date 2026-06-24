"""测试 LLM Service（双 Key 路由 + Failover）。"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel
from src.services.llm_service import LLMNode, LLMService

from pycore.core.exceptions import LLMError


class DummyTestSchema(BaseModel):
    """测试用 Schema（改名避免 pytest 收集）。"""

    name: str
    count: int


@pytest.fixture
def llm_service() -> LLMService:
    """创建测试 LLMService。"""
    return LLMService()


@pytest.mark.asyncio
async def test_chat_with_primary_key_success(llm_service: LLMService) -> None:
    """测试主 Key 成功。"""
    mock_provider = Mock()
    mock_provider.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": "Hello"}}]})
    mock_provider.extract_content = Mock(return_value="Hello")

    with patch.object(llm_service, "_get_provider", return_value=mock_provider):
        result = await llm_service.chat(
            LLMNode.QUEST_GENERATE,
            [{"role": "user", "content": "Hi"}],
        )

        assert result == "Hello"
        mock_provider.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_chat_fallback_to_secondary_key(llm_service: LLMService) -> None:
    """测试主 Key 失败，备 Key 成功。"""
    # 主 Key 失败
    mock_primary = Mock()
    mock_primary.chat_completion = AsyncMock(side_effect=LLMError("Primary failed"))

    # 备 Key 成功
    mock_fallback = Mock()
    mock_fallback.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": "Fallback OK"}}]})
    mock_fallback.extract_content = Mock(return_value="Fallback OK")

    with patch.object(llm_service, "_get_provider", side_effect=[mock_primary, mock_fallback]):
        result = await llm_service.chat(
            LLMNode.QUEST_GENERATE,
            [{"role": "user", "content": "Hi"}],
        )

        assert result == "Fallback OK"


@pytest.mark.asyncio
async def test_chat_both_keys_fail(llm_service: LLMService) -> None:
    """测试主备 Key 均失败。"""
    mock_provider = Mock()
    mock_provider.chat_completion = AsyncMock(side_effect=LLMError("API error"))

    with patch.object(llm_service, "_get_provider", return_value=mock_provider):
        with pytest.raises(LLMError) as exc_info:
            await llm_service.chat(
                LLMNode.QUEST_GENERATE,
                [{"role": "user", "content": "Hi"}],
            )

        assert "unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_chat_keys_missing(llm_service: LLMService) -> None:
    """测试 Key 缺失。"""
    # 临时清空 Key
    original_a = llm_service.key_a
    original_b = llm_service.key_b
    llm_service.key_a = ""
    llm_service.key_b = ""

    try:
        with pytest.raises(LLMError) as exc_info:
            await llm_service.chat(
                LLMNode.QUEST_GENERATE,
                [{"role": "user", "content": "Hi"}],
            )

        assert "not configured" in str(exc_info.value).lower()
    finally:
        llm_service.key_a = original_a
        llm_service.key_b = original_b


@pytest.mark.asyncio
async def test_chat_json_success(llm_service: LLMService) -> None:
    """测试 JSON 模式成功。"""
    mock_provider = Mock()
    mock_provider.chat_completion = AsyncMock(return_value={"choices": [{"message": {"content": '{"name": "test", "count": 42}'}}]})
    mock_provider.extract_content = Mock(return_value='{"name": "test", "count": 42}')

    with patch.object(llm_service, "_get_provider", return_value=mock_provider):
        result: DummyTestSchema = await llm_service.chat_json(  # type: ignore[assignment]
            LLMNode.QUEST_GENERATE,
            [{"role": "user", "content": "Generate"}],
            DummyTestSchema,
        )

        assert isinstance(result, DummyTestSchema)
        assert result.name == "test"
        assert result.count == 42


@pytest.mark.asyncio
async def test_chat_json_retry_on_invalid_json(llm_service: LLMService) -> None:
    """测试 JSON 解析失败后重试。"""
    mock_provider = Mock()
    mock_provider.chat_completion = AsyncMock(side_effect=[
        {"choices": [{"message": {"content": "not json"}}]},
        {"choices": [{"message": {"content": '{"name": "retry", "count": 1}'}}]},
    ])
    mock_provider.extract_content = Mock(side_effect=["not json", '{"name": "retry", "count": 1}'])

    with patch.object(llm_service, "_get_provider", return_value=mock_provider):
        result: DummyTestSchema = await llm_service.chat_json(  # type: ignore[assignment]
            LLMNode.QUEST_GENERATE,
            [{"role": "user", "content": "Generate"}],
            DummyTestSchema,
            max_retries=1,
        )

        assert result.name == "retry"
        assert result.count == 1


@pytest.mark.asyncio
async def test_node_routing(llm_service: LLMService) -> None:
    """测试节点路由正确性。"""
    assert llm_service.node_routing[LLMNode.QUEST_GENERATE] == ("A", "B")
    assert llm_service.node_routing[LLMNode.EVENT_COMPLETE] == ("A", "B")
    assert llm_service.node_routing[LLMNode.EVENT_DOWNGRADE] == ("B", "A")
    assert llm_service.node_routing[LLMNode.QUEST_REVIEW] == ("B", "A")
