# 项目经验

> 当前项目长期有效的经验。  
> Developer / Tester / Bugfix 在任务完成后维护本文件。

---

## Harness 系统经验摘要

新项目开始时，Developer / Tester / Bugfix 需要同时参考：

- 当前项目经验：`.sdd/experience.md`
- 系统级经验：`<Harness 根目录>/memory/harness-experience.md`

---

（项目经验将在开发过程中追加）

### [LLM 配置] 硅基流动双 Key（2026-06-24）
- **模型**：`Qwen/Qwen3.5-27B`，`LLM_BASE_URL=https://api.siliconflow.cn/v1`，OpenAI 兼容 `POST /v1/chat/completions`
- **密钥**：`LLM_API_KEY_A` / `LLM_API_KEY_B` 仅存 `backend/.env`；A 主责计划生成+完成反馈，B 主责降级+复盘，互为兜底
- **实现**：T-005 用 pycore `OpenAIProvider(base_url=..., api_key=...)`；`trust_env=False`；主 Key 失败再试 fallback Key
- **避坑**：禁止把 Key 写入 PRD/tasks.json/测试报告；聊天中泄露的 Key 建议用户定期轮换


### [T-002]: 前端全页面 Mock 闭环 P01–P08
- **陷阱**：完成反馈页若在 render 中直接 `navigate()` 会触发 React 警告；复盘页在 `review()` 后 quest 变 `completed`，`QuestFlowGuard` 仅检查 `in_progress` 会导致刷新被踢回首页。
- **经验**：Mock 状态统一存 `localStorage` key `goalslice_mock_state`；`eventService.advanceDayAfterFeedback()` 与原型一致，在 P05 确认后再推进 `current_day`；路由守卫需同时允许 `reviewGenerated + review` 访问 P07。
- **避坑**：Mock handler 必须按 endpoint 显式构造 DTO，不得直接返回内部实体；文案与 `docs/prototypes/index.html` 逐字对齐；`VITE_USE_MOCK=true` 时 services 不得走 axios 真实请求。
- **P03/P04 标题**：预览时间轴 Day3 用长标题（原型 WEEK_PLAN），每日任务卡片用短标题「用四格模板填空总结一场会」（api-contracts DailyEvent）；`DAILY_EVENT_TITLE_OVERRIDE` 在 `mockAcceptQuest` 时应用。
- **Sonnet 审查补全（2026-06-24）**：澄清页末题按钮统一「下一题」；末题可跳过提交。P04 本周进度仅顶栏展示；降级任务无输入区；P08 无资产时不展示擅自空态文案。P02 首题「← 返回上一页」、第 2–5 题「← 上一题」，返回时保留已选答案。

### [T-004]: 后端基础设施：Session + DB + 5 实体（2026-06-24）
- **陷阱**：SQLite 相对路径 `./data/goalslice.db` 在 `cd backend` 真实运行路径下会解析成 `backend/./data/goalslice.db`，导致联调时路径不一致。
- **经验**：`backend/src/db/session.py` 必须在创建引擎前将相对路径解析为绝对路径（`project_root / db_path_str`）并 `mkdir(parents=True, exist_ok=True)`；`backend/scripts/init_db.py` 使用 `src.*` 导入（非 `db.*` 裸导入），支持 `cd backend && PYTHONPATH=.. python3 scripts/init_db.py` 真实路径运行；测试需要 `greenlet` 依赖（`pip install greenlet`）。
- **避坑**：ORM 模型定义时，`status` / `total_days` / `current_day` 等有默认值的字段需同时设置 `default=` 和 `server_default=`（字符串）避免 SQLAlchemy 与数据库行为不一致；测试数据库必须与真实业务库隔离（使用临时文件或 `:memory:`），禁止测试清空 `backend/data/goalslice.db`。

### [T-005]: 硅基流动 LLM Provider 封装（2026-06-24）
- **陷阱**：用 `AsyncMock()` 包装整个 Provider 时，同步方法 `extract_content` 也会变成协程，导致 `chat()` 返回 coroutine 对象而非字符串。
- **经验**：`SiliconFlowProvider` 用 `httpx.AsyncClient(trust_env=False)` 直接调 OpenAI 兼容 `/chat/completions`，不依赖 openai SDK；`LLMService` 在代码内硬编码四节点主备 Key 路由（计划/反馈→A 主 B 兜，降级/复盘→B 主 A 兜）；Key 缺失时抛 `LLMError("LLM API keys not configured")`，由上层转 503；`chat_json` 支持 Pydantic Schema 校验 + 默认重试 1 次。
- **避坑**：Mock LLM Service 测试时，`chat_completion` 用 `AsyncMock`，`extract_content` / `parse_json_response` 用普通 `Mock`；测试类名勿用 `TestSchema` 前缀以免 pytest 误收集；枚举用 `StrEnum` 而非 `(str, Enum)` 以通过 ruff UP042。

### [Demo] 一键回到最开始（2026-06-24）
- **经验**：MVP 单线模型下 Demo 验收易被旧 session/副本卡住；顶栏 `VITE_DEMO_RESET=true` 时展示「回到最开始」，清空 `goalslice_mock_state` + 换新 `session_id` + `flowStore.reset()` 后 `location.reload()`。
- **避坑**：真实 API 下只换 session，不删 SQLite 旧数据；生产构建设 `VITE_DEMO_RESET=false` 隐藏按钮。

### [T-006]: 目标创建与澄清功能闭环（2026-06-24）
- **陷阱**：`pycore.api.responses.error_response` 返回 `(APIResponse, int)` 元组，FastAPI 路由直接 `return` 不会设置 HTTP 状态码，Tester 会看到 200；须改用 `JSONResponse(status_code=..., content={code,message,data})`。
- **陷阱（返工）**：ORM 新增列后 `create_all` 不会 `ALTER` 已有 SQLite 表；隔离测试库每次全量建表故 pytest 通过，但 `data/goalslice.db` 实库联调会 `no such column`。须在 `src/db/migrations.py` 幂等补列，并由 `init_db()` + 应用 `on_startup` 自动执行。
- **经验**：澄清进度恢复用 `GET /api/v1/goals/active`（session 作用域）+ `UserContext.clarify_answers_json` 存分批答案；`PATCH clarify` 仅在 5 题答案齐全时写 `refined_goal`；前端 P02 非 Mock 模式每题 `PATCH` 分批保存，刷新后从 `saved_answers` 恢复 step。
- **避坑**：`UserContext` 更新须先 `get_user_context` 再改字段，不能对 detached 实例 `merge` 后 `refresh`；Goal ORM 空字段用 `""` 存库、DTO 序列化时转 `null`；路由返回类型用 `-> Any`（FastAPI 不支持 `APIResponse | JSONResponse` 联合注解，mypy 仍可通过）。

### [T-007]: 计划生成与接受功能闭环（2026-06-24）
- **经验**：`POST /quests/generate` 用 `LLMService.chat_json` + `QuestPreviewLLMSchema`；预览 JSON 存 `goals.preview_json`；`POST /quests` 落库 Quest + 7 DailyEvent，Day1 `in_progress` 其余 `pending`；Day3 标题用 `DAILY_EVENT_TITLE_OVERRIDE` 对齐 P04。
- **避坑**：`goal_type=other` 返回 422 MVP 收窄；LLM Key 缺失返回 503「AI 服务暂时不可用」；测试用 `patch(_generate_with_llm)` 隔离 LLM，503 用例不 patch。

### [T-008]: 每日任务与完成反馈功能闭环（2026-06-24）
- **经验**：`GET /events/today` 按 session 活跃 quest 的 `current_day` 取唯一 `in_progress` event；`POST /events/{id}/complete` 写 `GrowthAsset`、将 event 标 `completed`、`current_day += 1` 并激活下一天 event（Day7 完成不推进）；`quest_summary.completed_days` 供 P04 顶栏 x/7；LLM 失败用 `feedback_templates` 静态 fallback（非 503）。
- **避坑**：Mock 下 P05 `advanceDayAfterFeedback()` 在确认后再推进 day；真实 API 下 complete 已推进 day，P05「好的，明天见」应 `navigate('/quest/today')` 而非 hub。
- **测试**：`test_events.py` 复用 accept quest 夹具 + `patch(_generate_feedback)`；完成后再 `GET today` 断言 day_index=2 与 DB `GrowthAsset` 计数。

### [T-009]: 任务降级功能闭环（2026-06-24）
- **经验**：`POST /events/{id}/downgrade` 用 `LLMNode.EVENT_DOWNGRADE` 生成 3 项方案（option_id 固定 5min/step1/tomorrow）；`PATCH apply-downgrade` 按 `option_id` 从 `downgrade_templates` 落库新 event，原 event 标 `downgraded`；`tomorrow` 选项不改 DB，前端本地提示。
- **避坑**：apply 后 `GET today` 靠 `status=in_progress` 命中新 event；降级后 `output_type=checkbox` 无输入区；完成降级任务仍走同一 `complete` 逻辑推进 day。
- **测试**：`test_apply_downgrade_replaces_event` 断言 `original_event_id` 与 DB 原 event `downgraded`；`test_downgraded_complete_advances_day` 验证降级完成仍推进。

### [T-010]: 进行中枢与成长资产功能闭环（2026-06-24）
- **经验**：`GET /quests/active` 无副本时 `data=null`（200）；`GET /quests/{id}` 返回 7 日 `days` 摘要；`GET /assets?quest_id=` 按 session 筛选；路由守卫非 Mock 时统一 `questService.getActive()` 驱动首页→P08 重定向。
- **避坑**：同日多 event（降级后）用 `_primary_event_for_day` 优先 `in_progress`；P08 无资产时不展示擅自空态文案；`has_in_progress_quest_for_session` 已在 accept 时校验 MVP 单副本。
- **测试**：`test_get_active_quest_null_when_none`；完成一次任务后 `test_list_assets_by_quest` 断言资产落库。

### [T-011]: 周复盘与开启下周功能闭环（2026-06-24）
- **经验**：`POST /quests/{id}/review` Day7 完成后生成复盘并设 `quest.status=completed`，结果缓存 `review_json`；`next-week` 复用 goal 设 `active` 并清 `preview_json`，返回 `redirect=clarify`；`pause` 设 quest `abandoned` + goal `paused`。
- **避坑**：P07 移除 `QuestFlowGuard`（review 后 `getActive` 为 null）；`flowStore.reviewQuestId` 支持复盘页刷新；LLM 失败用 `review_templates` fallback（200）。
- **测试**：`test_review.py` 循环 complete 7 天后 review；`test_pause_quest` 断言 active 为 null。

### [T-012]: E2E 全链路回归 + startup.md（2026-06-24）
- **经验**：`docs/startup.md` 区分 Agent 端口 5199/8099 与用户门禁 5175/8003；`VITE_USE_MOCK` 切换须重启 Vite；`test_e2e.py` 用 TestClient 覆盖 P01→P07、暂停、503、降级、中枢 API。
- **避坑**：E2E 不替代各任务首次浏览器门禁；`quests/generate` 503 与 complete/review fallback 行为不同，startup 文档须分表说明。
- **命令**：`PYTHONPATH=.. ../.venv/bin/python -m pytest tests/test_e2e.py -v`
