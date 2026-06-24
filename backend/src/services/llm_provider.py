"""硅基流动 LLM Provider（基于 httpx,OpenAI 兼容）。

直接使用 httpx 调用，不依赖 openai SDK，确保 trust_env=False。
"""

import json
from typing import Any, cast

import httpx

from pycore.core.exceptions import LLMError
from pycore.core.logger import get_logger

logger = get_logger()


class SiliconFlowProvider:
    """硅基流动 OpenAI 兼容 Provider。

    使用 httpx 直接调用 /v1/chat/completions，确保 trust_env=False。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        model: str = "Qwen/Qwen3.5-27B",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """调用 chat completions API。

        Args:
            messages: OpenAI 格式消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Returns:
            API 响应 JSON

        Raises:
            LLMError: API 调用失败
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        try:
            async with httpx.AsyncClient(trust_env=False, timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())

        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail = f"{error_detail}: {error_body.get('error', {}).get('message', str(error_body))}"
            except Exception:
                error_detail = f"{error_detail}: {e.response.text[:200]}"

            logger.error("SiliconFlow API error", status=e.response.status_code, detail=error_detail)
            raise LLMError(
                error_detail,
                provider="siliconflow",
                model=self.model,
            ) from e

        except httpx.TimeoutException as e:
            logger.error("SiliconFlow timeout", timeout=self.timeout)
            raise LLMError(
                f"Request timeout after {self.timeout}s",
                provider="siliconflow",
                model=self.model,
            ) from e

        except Exception as e:
            logger.error("SiliconFlow unexpected error", error=str(e))
            raise LLMError(
                f"Unexpected error: {e}",
                provider="siliconflow",
                model=self.model,
            ) from e

    def extract_content(self, response: dict[str, Any]) -> str:
        """从 API 响应提取 content。

        Args:
            response: API 响应 JSON

        Returns:
            助手回复内容

        Raises:
            LLMError: 响应结构异常
        """
        try:
            content = response["choices"][0]["message"]["content"]
            return cast(str, content)
        except (KeyError, IndexError, TypeError) as e:
            logger.error("Invalid response structure", response=response)
            raise LLMError(
                f"Invalid response structure: {e}",
                provider="siliconflow",
                model=self.model,
            ) from e

    def parse_json_response(self, content: str) -> dict[str, Any]:
        """解析 JSON 格式的响应内容。

        Args:
            content: LLM 返回的文本内容

        Returns:
            解析后的 JSON 对象

        Raises:
            LLMError: JSON 解析失败
        """
        try:
            result: dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            logger.error("JSON parse error", content=content[:200], error=str(e))
            raise LLMError(
                f"JSON parse error: {e}",
                provider="siliconflow",
                model=self.model,
            ) from e
