# 测试报告：T-006 目标创建与澄清功能闭环

**测试时间**：2026-06-24 23:53（第 2 次独立验证，Developer 返工后）
**Tester Agent ID**：composer-2.5-tester（主会话代行）

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | P01 输入目标点击开始 → 跳转 P02 | PASS | `HomePage.tsx:19-26` 调用 `goalService.createGoal` 后 `navigate('/clarify')`；隔离库 `test_create_goal_success` HTTP 200 |
| AC-2 | P01 点击示例 Chip 自动填入文案 | PASS | `HomePage.tsx:46-54` `EXAMPLE_CHIPS` + `setRawGoal(chip.goal)` |
| AC-3 | P02 逐题选择/跳过 5 题，提交后跳转 P03 | PASS | `ClarifyPage.tsx` 5 题流；`submitClarify` → `navigate('/quest/preview')`；`test_clarify_goal_success` 全绿 |
| AC-4 | 刷新后澄清进度可从后端恢复（同 session_id） | PASS | 旧 schema 实库 smoke：`PATCH partial` 200 → `GET /goals/active` 200 含 `saved_answers.goal_type=技能提升`；`test_get_active_goal_with_saved_answers` 通过；`ClarifyPage.tsx:50-65` 非 Mock 模式从 `getActiveGoal` 恢复 step |
| AC-5 | 进行中副本时新建目标显示 422 友好提示 | PASS | `test_create_goal_conflict_when_quest_in_progress` HTTP 422 + message 含「进行中」；`HomePage.tsx:28` `message.error` 展示 |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `pytest backend/tests`（goals/clarify） | PASS | **43 passed**（含 `test_goals.py` 6 项 + `test_migrations.py` 2 项） |
| TC-2 | `npm run type-check / lint / build` | PASS | type-check 0 error；lint 3 warnings（既有，非 error）；build 成功 |
| TC-3 | `VITE_USE_MOCK=false` 时 P01/P02 走真实 API | PASS | `goalService.ts:20-41` `useMock=false` 分支调用 `api.post/patch/get`，动态 import `api` 不命中 mock handler |
| TC-4 | `vite.config.ts` proxy `/api` → 8099/8003 | PASS | `server.proxy['/api']` 默认 `8099`；`VITE_BACKEND_PROXY_TARGET` 可切 `8003` |
| TC-5 | `VITE_API_BASE_URL=/api` | PASS | `frontend/.env` 已配置 |
| TC-6 | P01/P02 无 `[Mock]` 残留文案 | PASS | `frontend/src/pages/` 无 `[Mock]` 字符串 |
| TC-7 | 响应格式符合 api-contracts.md | PASS | `POST /goals` 返回 `goal` + `clarify_questions`（5 题）；`PATCH clarify` 返回 `goal` + `context`；分批 PATCH 返回 200 |
| TC-8 | LLM 联调 | N/A | 本任务澄清题不调用 LLM；标注 **未执行真实 LLM 联调** |
| TC-9 | `$PY -m mypy backend/src backend/tests` | PASS | 31 source files，0 issues；`goals.py` 三处路由已补 `-> Any` |
| TC-实库 | 旧 schema 迁移 + 联调 | PASS | 模拟 T-004 旧库（无 `clarify_answers_json`）经 `on_startup(init_db)` 后：`POST/PATCH/GET active` 全 200，无 `OperationalError` |

## 返工问题复验（对比第 1 次 FAIL）

| 上轮问题 | 本轮状态 | 证据 |
|---------|---------|------|
| BUG-1 实库缺 `clarify_answers_json` | **已修复** | `migrations.py` 幂等 `ALTER TABLE`；`init_db()` + `main.py` `on_startup(init_db)`；`test_migrations.py` 2/2 通过；旧库 API smoke 通过 |
| BUG-2 mypy `no-untyped-def` | **已修复** | `goals.py:33,49,61` 均为 `-> Any`；mypy 全绿 |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 密钥泄露 | PASS | 产出代码与报告无真实 Key |
| 分层结构 | PASS | `routes → service → repository → models` |
| 测试库隔离 | PASS | `test_goals.py` 使用临时 SQLite + `dependency_overrides`；无 `drop_all` 清业务库 |
| pycore 合规 | PASS | `APIServer` + `ConfigManager` + 模板扩展 |
| httpx trust_env | PASS | T-006 不涉及新增外部 HTTP 调用 |

## 真实联调证据（旧 schema 模拟业务库）

```
on_startup → init_db → apply_sqlite_migrations
POST /api/v1/goals                    → HTTP 200, code=200
PATCH /api/v1/goals/{id}/clarify      → HTTP 200（分批保存）
GET  /api/v1/goals/active             → HTTP 200, saved_answers.goal_type=技能提升
PATCH /api/v1/goals/{id}/clarify      → HTTP 200, refined_goal=提升会议总结能力
```

## 用户门禁（user_gate）

任务标记 `user_gate: true`。Agent 侧 API/代码验证已全部 PASS。

**待用户确认**：请将 `frontend/.env` 设为 `VITE_USE_MOCK=false`，启动后端（8099）+ 前端（5199），在浏览器完成 P01→P02→P03 全链路并刷新验证澄清进度恢复。

## 验证命令摘要

```
ruff check backend/src backend/tests     → All checks passed
mypy backend/src backend/tests           → Success: no issues found in 31 source files
pytest backend/tests                     → 43 passed
npm run type-check / lint / build        → PASS（lint 3 warnings）
旧 schema API smoke                      → POST/PATCH/GET active 全 200
```
