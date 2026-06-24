"""GoalSlice LLM Service（硅基流动双 Key 路由 + Failover）。

按节点路由主备 Key：
- quest_generate（计划生成）、event_complete（完成反馈）→ Key A 主 / Key B 兜底
- event_downgrade（任务降级）、quest_review（周复盘）→ Key B 主 / Key A 兜底
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ValidationError

from pycore.core.exceptions import LLMError
from pycore.core.logger import get_logger
from src.core.config import get_settings
from src.services.llm_provider import SiliconFlowProvider

logger = get_logger()


class LLMNode(StrEnum):
    """LLM 业务节点枚举。"""

    QUEST_GENERATE = "quest_generate"  # 计划生成
    EVENT_COMPLETE = "event_complete"  # 完成反馈
    EVENT_DOWNGRADE = "event_downgrade"  # 任务降级
    QUEST_REVIEW = "quest_review"  # 周复盘


class LLMService:
    """GoalSlice LLM 服务（双 Key 路由 + Failover）。"""

    def __init__(self) -> None:
        settings = get_settings()

        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self.key_a = settings.llm_api_key_a
        self.key_b = settings.llm_api_key_b

        # 节点 → 主备 Key 映射
        self.node_routing = {
            LLMNode.QUEST_GENERATE: ("A", "B"),
            LLMNode.EVENT_COMPLETE: ("A", "B"),
            LLMNode.EVENT_DOWNGRADE: ("B", "A"),
            LLMNode.QUEST_REVIEW: ("B", "A"),
        }

    def _get_provider(self, key_name: str) -> SiliconFlowProvider | None:
        """根据 Key 名称获取 Provider。

        Args:
            key_name: "A" 或 "B"

        Returns:
            Provider 实例，Key 缺失时返回 None
        """
        api_key = self.key_a if key_name == "A" else self.key_b
        if not api_key or not api_key.strip():
            return None

        return SiliconFlowProvider(
            api_key=api_key,
            base_url=self.base_url,
            model=self.model,
        )

    async def chat(
        self,
        node: LLMNode,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """发送聊天请求（主备 Key Failover）。

        Args:
            node: 业务节点（用于路由主备 Key）
            messages: OpenAI 格式消息
            temperature: 温度
            max_tokens: 最大 token
            **kwargs: 其他参数

        Returns:
            LLM 回复内容

        Raises:
            LLMError: 主备 Key 均失败或均缺失，HTTP 503
        """
        primary_key, fallback_key = self.node_routing[node]

        # 尝试主 Key
        primary_provider = self._get_provider(primary_key)
        if primary_provider:
            try:
                response = await primary_provider.chat_completion(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = primary_provider.extract_content(response)
                logger.info(
                    "LLM success",
                    node=node.value,
                    key=f"Key_{primary_key}",
                    model=self.model,
                )
                return content

            except LLMError as e:
                logger.warning(
                    "Primary key failed, trying fallback",
                    node=node.value,
                    primary=primary_key,
                    fallback=fallback_key,
                    error=str(e),
                )

        # 主 Key 失败或缺失，尝试备 Key
        fallback_provider = self._get_provider(fallback_key)
        if fallback_provider:
            try:
                response = await fallback_provider.chat_completion(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = fallback_provider.extract_content(response)
                logger.info(
                    "LLM success (fallback)",
                    node=node.value,
                    key=f"Key_{fallback_key}",
                    model=self.model,
                )
                return content

            except LLMError as e:
                logger.error(
                    "Both keys failed",
                    node=node.value,
                    error=str(e),
                )
                raise LLMError(
                    f"LLM service unavailable: {e}",
                    provider="siliconflow",
                    model=self.model,
                ) from e

        # 主备 Key 均缺失
        logger.error("LLM keys missing", node=node.value, primary=primary_key, fallback=fallback_key)
        raise LLMError(
            "LLM API keys not configured",
            provider="siliconflow",
            model=self.model,
        )

    async def chat_json(
        self,
        node: LLMNode,
        messages: list[dict[str, str]],
        schema_model: type[BaseModel],
        temperature: float = 0.7,
        max_retries: int = 1,
        **kwargs: Any,
    ) -> BaseModel:
        """发送聊天请求并解析 JSON（Schema 校验 + 重试）。

        Args:
            node: 业务节点
            messages: OpenAI 格式消息
            schema_model: Pydantic 模型用于校验
            temperature: 温度
            max_retries: JSON 解析失败后的最大重试次数
            **kwargs: 其他参数

        Returns:
            校验后的 Pydantic 模型实例

        Raises:
            LLMError: 调用失败或 JSON 校验失败（超过重试次数）
        """
        for attempt in range(max_retries + 1):
            content = await self.chat(
                node,
                messages,
                temperature=temperature,
                **kwargs,
            )

            # 尝试解析 JSON
            try:
                provider = SiliconFlowProvider(api_key="dummy", base_url=self.base_url, model=self.model)
                json_data = provider.parse_json_response(content)
                validated = schema_model(**json_data)
                logger.info("JSON validated", node=node.value, attempt=attempt + 1)
                return validated

            except (ValidationError, LLMError) as e:
                if attempt < max_retries:
                    logger.warning(
                        "JSON validation failed, retrying",
                        node=node.value,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    continue

                logger.error(
                    "JSON validation failed after retries",
                    node=node.value,
                    retries=max_retries,
                    error=str(e),
                )
                raise LLMError(
                    f"JSON validation failed after {max_retries + 1} attempts: {e}",
                    provider="siliconflow",
                    model=self.model,
                ) from e

        # Should not reach here
        raise LLMError("Unexpected error in chat_json", provider="siliconflow", model=self.model)
