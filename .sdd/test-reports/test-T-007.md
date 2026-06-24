# 测试报告：T-007 计划生成与接受功能闭环

**测试时间**：2026-06-25 00:14（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester（主会话代行）

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | P03 展示 7 天主线标题、通关条件、每日列表（含 Day7 Boss） | PASS | `test_generate_quest_success` 返回 7 天且 `days[6].is_boss=true`；`QuestPreviewPage.tsx` 时间轴渲染 `is_boss` + `Boss 战 ·` 前缀 |
| AC-2 | P03 点击「重新生成」展示新计划 | PASS | `handleRegenerate` 调用 `questService.generatePreview`；smoke 连续两次 `POST /quests/generate` 均 200 |
| AC-3 | 接受计划后跳转 P04 显示 Day1 | PASS | `handleAccept` → `acceptQuest` → `navigate('/quest/today')`；`test_accept_quest_persists_quest_and_events` 返回 `today_event.day_index=1`、`status=in_progress`；按钮文案「开始 Day 1」与原型一致 |
| AC-4 | 非 MVP 目标 P03 展示 422 友好收窄 | PASS | `test_generate_quest_out_of_scope` HTTP 422；`QuestPreviewPage` `loadError` 态展示 message +「返回澄清页」 |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `pytest backend/tests`（quests） | PASS | **48 passed**；`test_quests.py` 5 项全绿 |
| TC-2 | `npm run type-check / lint / build` | PASS | type-check 0 error；lint 3 warnings（既有）；build 成功 |
| TC-3 | `VITE_USE_MOCK=false` 时 P03 走真实 API | PASS | `questService.generatePreview/acceptQuest` 在 `useMock=false` 分支调用 `api.post('/v1/quests/generate')` 与 `api.post('/v1/quests')` |
| TC-4 | LLM Key 可用时真实 JSON；缺失 503 + 前端降级 | PASS（503） | `test_generate_quest_llm_unavailable` → HTTP 503「AI 服务暂时不可用」；P03 `loadError` 展示 AI 服务文案。**未执行真实 LLM 联调**（Key 状态未在本次环境验证） |
| TC-5 | 接受后 SQLite 持久化 Quest + 7 DailyEvent | PASS | `test_accept_quest_persists_quest_and_events` 实查隔离库 7 条 `daily_events` |
| TC-6 | P03 无 `[Mock]` 残留 | PASS | `QuestPreviewPage.tsx` 无 `[Mock]` 字符串；非 Mock 路径不 import mock handler |
| TC-7 | 响应格式符合 api-contracts.md | PASS | generate 返回 `preview` 含 `quest_title/success_condition/total_estimated_time/days`；accept 返回 `quest` + `today_event` |
| TC-8 | `mypy` / `ruff` | PASS | 37 source files 0 issue；ruff All checks passed |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 密钥泄露 | PASS | 产出无真实 Key |
| 分层结构 | PASS | `routes/quests.py → QuestService → repositories` |
| LLM 路由 | PASS | `LLMNode.QUEST_GENERATE` 走 Key A 主 B 兜（`llm_service.py`） |
| 测试库隔离 | PASS | 隔离临时 SQLite + `dependency_overrides` |
| 迁移 | PASS | `goals.preview_json` 幂等补列于 `migrations.py` |

## 真实联调证据（API smoke，Mock LLM）

```
POST /api/v1/quests/generate  → 200, 7 days, day7 is_boss
POST /api/v1/quests/generate  → 200（重新生成）
POST /api/v1/quests           → 200, today_event.day_index=1, quest.status=in_progress
POST /api/v1/quests/generate（goal_type=其他）→ 422 MVP 收窄提示
```

## LLM 联调说明

- **真实 LLM 联调**：未执行（测试环境未验证 Key 可用性）
- **503 路径**：已验证（无 Key / LLM 不可用时返回 503，前端有降级 UI）
- **单测 LLM**：使用 `patch(_generate_with_llm)` 隔离，符合 T-005 经验

## 用户门禁（user_gate）

任务标记 `user_gate: true`。Agent 侧 API/代码验证已全部 PASS。

**待用户确认**：`VITE_USE_MOCK=false` 下浏览器走 P02 澄清完成 → P03 预览 → 重新生成 → 开始 Day 1 → P04。

## 验证命令摘要

```
ruff / mypy     → PASS
pytest          → 48 passed
npm type-check / lint / build → PASS
API smoke       → generate×2 + accept + 422 out-of-scope 全通过
```
