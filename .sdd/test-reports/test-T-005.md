# 测试报告：T-005 后端基础设施：硅基流动 LLM Provider 封装

**测试时间**：2026-06-24 23:20（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester（主会话代行，子代理中断后补验）

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | LLM Provider 从 `backend/.env` 读取 `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL`，代码无硬编码 Key | PASS | `LLMService.__init__` 通过 `get_settings()` 读取 `llm_api_key_a/b`、`llm_base_url`、`llm_model`（`llm_service.py:34-39`）；`AppSettings` 字段定义于 `config.py:63-66`；`backend/src` 无真实 Key，仅 `chat_json` 内 `api_key="dummy"` 占位用于 JSON 解析 |
| AC-2 | httpx 客户端 `trust_env=False`，避免代理环境变量干扰 | PASS | `llm_provider.py:74` `httpx.AsyncClient(trust_env=False, timeout=...)`；单测 `test_llm_provider.py::test_chat_completion_success` 断言 `trust_env=False` |
| AC-3 | `LLM_API_KEY` 缺失时服务层返回 503 或明确 fallback，不静默吞错 | PASS | Key 均缺失时抛 `LLMError("LLM API keys not configured")`（`llm_service.py:153-157`）；单测 `test_chat_keys_missing` 覆盖；上层路由可在 T-006+ 映射为 HTTP 503 |
| AC-4 | Provider 支持结构化 JSON 响应解析与校验失败重试 | PASS | `SiliconFlowProvider.parse_json_response` + `LLMService.chat_json` 使用 Pydantic `schema_model` 校验；`max_retries=1` 默认重试 1 次（`llm_service.py:168-218`）；单测 `test_chat_json_success`、`test_chat_json_retry_on_invalid_json` 通过 |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `$PY -m ruff check backend/src backend/tests` 通过 | PASS | exit 0：`All checks passed!` |
| TC-2 | `$PY -m mypy backend/src backend/tests` 通过 | PASS | exit 0：`Success: no issues found in 21 source files` |
| TC-3 | `$PY -m pytest backend/tests` 通过（含 Key 缺失 fallback 单测） | PASS | 35 passed in 0.56s；T-005 相关 14 项单测全部通过 |
| TC-4 | httpx 调用处 `trust_env=False` 已落实 | PASS | 见 AC-2 |
| TC-5 | 必要 Key 未硬编码进代码；真实 Key 仅存在于 `backend/.env` | PASS | `grep` 扫描 `backend/src` 无真实 Key；`.env` 未读取/未打印 |
| TC-6 | Key 缺失时测试报告标记 Mock/fallback 验收，不得宣称真实 LLM 联调通过 | PASS | **本轮未执行真实硅基流动 API 调用**；failover / Key 缺失 / JSON 重试均通过 Mock 单测验收 |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 文件存在性 | PASS | `backend/src/services/llm_provider.py`、`llm_service.py`、`__init__.py`；`backend/tests/test_llm_provider.py`、`test_llm_service.py` 均已创建 |
| 密钥泄露 | PASS | 产出代码与 `.sdd/**` 无真实 Key；`pycore/` 文档示例含 `sk-...` 占位，非本项目业务代码 |
| TODO/FIXME/HACK | PASS | `backend/src/services/*` 无匹配 |
| 节点路由 | PASS | 计划/反馈 → A 主 B 兜；降级/复盘 → B 主 A 兜（`test_node_routing`） |
| 主备 Failover | PASS | `test_chat_fallback_to_secondary_key`、`test_chat_both_keys_fail` 通过 |

## 外部服务联调说明

| 项目 | 状态 |
|------|------|
| 硅基流动真实 API 调用 | **未执行**（按任务 notes：`fallback_allowed=true if key missing`；技术检查要求 Mock/fallback 验收即可） |
| Mock/fallback 单测 | PASS（Key 缺失、主 Key 失败 failover、JSON 重试） |

## 验证命令输出摘要

```
# ruff (PASS)
All checks passed!

# mypy (PASS)
Success: no issues found in 21 source files

# pytest 全量 (PASS)
35 passed in 0.56s

# pytest T-005 专项 (PASS)
14 passed in 0.16s
  - test_llm_provider.py: 7 passed
  - test_llm_service.py: 7 passed
```

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | `chat_json` 为解析 JSON 临时实例化 `SiliconFlowProvider(api_key="dummy")` | llm_service | 后续可抽静态 `parse_json_response` 避免 dummy Key |
| 2 | 服务层抛 `LLMError`，HTTP 503 映射待 T-006+ 路由层实现 | api/routes | 后续任务接入时统一错误处理 |
| 3 | `.env.example` 含 `LLM_NODE_*` 路由变量，代码内硬编码路由表 | config | 若需可配置化，后续修整任务处理 |
