# 测试报告：T-009 任务降级功能闭环

**测试时间**：2026-06-25 00:38（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | P04 点击「今天太难了，帮我降级」弹出 Modal 展示 1–3 个 AI 降级方案 | PASS | `QuestTodayPage.tsx:65-74` `handleOpenDowngrade` → `eventService.getDowngradeOptions` → `DowngradeModal` 渲染 `options`；`test_downgrade_options_success` 断言 3 项且 `option_id` 为 `5min/step1/tomorrow` |
| AC-2 | 选择方案确认后 Modal 关闭，P04 显示替换后更小任务 | PASS | `handleApplyDowngrade` → `applyDowngrade` → `loadToday()` 刷新；`test_apply_downgrade_replaces_event` 断言新 `event_title` 含「5 分钟版」、`GET /events/today` 返回新 `event_id` |
| AC-3 | 完成降级任务后点「我已经完成」正常进入 P05，进度仍推进 | PASS | 共用 `handleComplete` → `complete` → `navigate('/quest/feedback')`；`test_downgraded_complete_advances_day` 完成后 `completed_days=1`、`day_index=2` |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `pytest`（downgrade/apply-downgrade） | PASS | 全量 **57 passed**；`test_events.py` 降级相关 4 项全绿 |
| TC-2 | `npm run type-check / lint / build` | PASS | type-check 0 error；lint 3 warnings（既有 react-refresh）；build 成功 |
| TC-3 | `VITE_USE_MOCK=false` 命中 downgrade 与 apply-downgrade | PASS | `eventService.ts:47-68` 在 `useMock=false` 时 `POST /v1/events/{id}/downgrade` 与 `PATCH /v1/events/{id}/apply-downgrade`；`vite.config.ts` 含 `/api` 代理；`VITE_API_BASE_URL=/api` |
| TC-4 | apply-downgrade 后新 event `status=in_progress` 且 `original_event_id` 指向原任务 | PASS | `event_service.py:197-215` 创建新 event；`test_apply_downgrade_replaces_event` 断言 `status=in_progress`、`original_event_id==event_id`、原 event `status=downgraded` |
| TC-5 | 降级完成仍推进 `current_day` 与资产发放 | PASS | 降级后完成走同一 `complete_event` 路径（`GrowthAsset` 写入 + `quest.current_day` 推进）；`test_downgraded_complete_advances_day` 断言 Day2；与 `test_complete_event_success` 资产逻辑一致 |
| TC-6 | 页面无 `[Mock]` 残留；P04 无「后续版本」拦截 | PASS | `frontend/src` 无 `[Mock]`；全局无「后续版本」字符串；`QuestTodayPage` 降级按钮直接调用真实 API |
| TC-7 | LLM Key 可用时真实生成；缺失时 fallback | PASS（fallback） | `event_service.py:250-261` 捕获 `LLMError` → `get_static_downgrade_options()` 静态方案仍 200；`LLMNode.EVENT_DOWNGRADE` 路由 B 主/A 备（`test_llm_service.py`）；**未执行真实硅基流动 HTTP 联调** |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| API 路由与契约 | PASS | `events.py:61-92` 实现 downgrade/apply-downgrade；字段对齐 `docs/api-contracts.md` |
| 密钥泄露 | PASS | `backend/src` 无硬编码 Key；报告不复述 Key |
| 分层结构 | PASS | `routes/events.py → EventService → EventRepository` |
| httpx trust_env | PASS | LLM Provider `trust_env=False`（继承 T-005） |
| 测试库隔离 | PASS | `test_events.py` 临时 SQLite + `dependency_overrides[get_db]`；无 `drop_all` 作用于运行时库 |
| TODO/FIXME | PASS | 降级相关源码无 TODO/FIXME/HACK |

## 真实联调证据

### pytest TestClient（隔离库，完整降级闭环）

```
POST /events/{id}/downgrade        → 200, 3 options
PATCH /events/{id}/apply-downgrade → 200, new event in_progress, original_event_id 正确
GET  /events/today                 → 200, 返回新 event
POST /events/{new_id}/complete     → 200, completed_days=1
GET  /events/today                 → 200, day_index=2
```

### uvicorn smoke（8099，部分）

- 种子流程在 `POST /quests/generate` 因 LLM 不可用返回 **503**（generate 无 fallback，与 T-007 一致）
- 降级端点本身在单测与代码审查中已完整验证；全链路浏览器联调待用户门禁

## LLM 联调说明

| 场景 | 结果 |
|------|------|
| Key 配置状态 | 已配置（backend/.env，未复述） |
| 真实 HTTP 联调 | **未执行**（Tester 环境网络受限；generate smoke 亦 503） |
| LLM 不可用路径 | **fallback**（`request_downgrade` 静态 3 方案，HTTP 200，非 503） |
| 单测覆盖 | `test_downgrade_options_success`、`test_apply_downgrade_replaces_event`、`test_downgraded_complete_advances_day` |

对比：`quests/generate` LLM 失败返回 503；`events/downgrade` 采用静态 fallback，符合 technicalChecks「缺失时 fallback」。

## 用户门禁（user_gate）

任务标记 `user_gate: true`。Agent 侧代码、单测与静态联调路径已全部 PASS。

**待用户确认**（用户门禁端口 5175/8003）：

1. `frontend/.env` 或 `.env.local` 设 `VITE_USE_MOCK=false`
2. 启动后端 `8003`、前端 `5175`（`VITE_BACKEND_PROXY_TARGET=http://localhost:8003`）
3. 在 P04 点击「今天太难了，帮我降级」→ 选择方案 → 确认后任务标题/用时更新
4. 完成降级任务 → 进入 P05 查看反馈与进度推进
5. 可选：LLM 可用时确认降级方案为 AI 生成（非静态 fallback 文案）

## 验证命令摘要

```
ruff check backend/src backend/tests  → All checks passed
mypy backend/src backend/tests        → Success: 44 files
pytest backend/tests                  → 57 passed
pytest -k downgrade                   → 4 passed
npm run type-check                    → 0 errors
npm run lint                          → 0 errors (3 warnings)
npm run build                         → success
```
