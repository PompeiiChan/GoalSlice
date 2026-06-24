"""测试 LLM Provider（httpx 直接调用）。"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from src.services.llm_provider import SiliconFlowProvider

from pycore.core.exceptions import LLMError


@pytest.fixture
def provider() -> SiliconFlowProvider:
    """创建测试 Provider。"""
    return SiliconFlowProvider(
        api_key="test-key",
        base_url="https://api.test.com/v1",
        model="test-model",
    )


@pytest.mark.asyncio
async def test_chat_completion_success(provider: SiliconFlowProvider) -> None:
    """测试成功调用。"""
    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello!",
                }
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_post = AsyncMock(return_value=AsyncMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None,
        ))
        mock_client.return_value.__aenter__.return_value.post = mock_post

        response = await provider.chat_completion([{"role": "user", "content": "Hi"}])

        assert response == mock_response
        mock_client.assert_called_once_with(trust_env=False, timeout=30.0)


@pytest.mark.asyncio
async def test_chat_completion_http_error(provider: SiliconFlowProvider) -> None:
    """测试 HTTP 错误。"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock(
            status_code=500,
            json=lambda: {"error": {"message": "Server error"}},
            text="Server error",
        )
        mock_post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500 error",
                request=AsyncMock(),
                response=mock_response,
            )
        )
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with pytest.raises(LLMError) as exc_info:
            await provider.chat_completion([{"role": "user", "content": "Hi"}])

        assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_chat_completion_timeout(provider: SiliconFlowProvider) -> None:
    """测试超时。"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.return_value.__aenter__.return_value.post = mock_post

        with pytest.raises(LLMError) as exc_info:
            await provider.chat_completion([{"role": "user", "content": "Hi"}])

        assert "timeout" in str(exc_info.value).lower()


def test_extract_content_success(provider: SiliconFlowProvider) -> None:
    """测试提取内容成功。"""
    response = {
        "choices": [
            {
                "message": {
                    "content": "Test content",
                }
            }
        ]
    }

    content = provider.extract_content(response)
    assert content == "Test content"


def test_extract_content_invalid_structure(provider: SiliconFlowProvider) -> None:
    """测试响应结构异常。"""
    with pytest.raises(LLMError):
        provider.extract_content({"invalid": "response"})


def test_parse_json_response_success(provider: SiliconFlowProvider) -> None:
    """测试 JSON 解析成功。"""
    content = '{"key": "value"}'
    result = provider.parse_json_response(content)
    assert result == {"key": "value"}


def test_parse_json_response_invalid(provider: SiliconFlowProvider) -> None:
    """测试 JSON 解析失败。"""
    with pytest.raises(LLMError):
        provider.parse_json_response("not json")
