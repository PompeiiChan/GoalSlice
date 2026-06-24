# 测试报告：T-011 周复盘与开启下周功能闭环

**测试时间**：2026-06-25 01:28（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | 用户完成 Day7 任务后在周复盘页（P07）看到本周完成汇总、产出列表、AI 观察、Boss 总结与下周副本推荐 | PASS | `QuestFeedbackPage.tsx:39-40` Day7 完成跳转 `/quest/review`；`QuestReviewPage.tsx:88-125` 展示 Boss 总结、完成小事件/产出物统计、产出列表、成长资产、`observations[0]`、下周建议标题与描述；数据来自 `questService.review()` |
| AC-2 | 用户在 P07 点击「开启下一周副本」，页面进入澄清或计划流程（P02/P03），准备开始新一周 | PASS | `QuestReviewPage.tsx:52-58` 调用 `questService.nextWeek`，`redirect === 'clarify'` 时 `navigate('/clarify')`；后端 `start_next_week` 返回 `redirect: "clarify"` 并复用 goal、`goal.status=active`（`test_next_week_after_review`） |
| AC-3 | 用户在 P07 点击「暂停，下次再说」，页面回到首页（P01），当前副本不再作为活跃副本 | PASS | `QuestReviewPage.tsx:66-71` 调用 `pause` 后 `navigate('/')`；`test_pause_quest` 断言 quest `abandoned`、`GET /quests/active` 返回 `data=null` |
| AC-4 | 用户暂停后再次访问，首页展示目标输入而非强制进入中枢 | PASS | `HomeRouteGuard` 非 Mock 时 `getActive()` 为 null 不跳转 hub（`guards.tsx:19-23`）；暂停后 goal `paused`、无 in_progress quest，符合 AC |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `pytest backend/tests`（review/next-week/pause） | PASS | 全量 **67 passed**；`test_review.py` 4 项（review 成功、未就绪 422、next-week、pause）全绿 |
| TC-2 | `npm run type-check / lint / build` | PASS | type-check 0 error；lint 3 warnings（既有 react-refresh）；build 成功 |
| TC-3 | `VITE_USE_MOCK=false` 时 P07 命中 review、next-week、pause 真实端点 | PASS | `questService.ts:80-106` 非 Mock 分支 POST `/v1/quests/{id}/review|next-week|pause`；`QuestReviewPage.tsx` 三处调用 |
| TC-4 | review 后 quest status=completed；next-week 返回 redirect；pause 后 quest abandoned、goal paused | PASS | `quest_service.py:270-273` 设 completed；`test_review_quest_success` DB 断言；`test_next_week_after_review` redirect=clarify；`test_pause_quest` abandoned + goal paused |
| TC-5 | 页面无 `[Mock]` 残留 | PASS | `frontend/src` 全局 grep 无 `[Mock]` 字符串 |
| TC-6 | LLM Key 可用时复盘文案为真实生成；缺失时 fallback | PASS（fallback 已验证） | `backend/.env` 已配置 LLM_API_KEY_A/B 与 QUEST_REVIEW 节点路由；沙箱 pytest 网络受限，review 走 `build_static_review` fallback（`_generate_review` except LLMError）；独立脚本 patch `LLMService.chat_json` 抛错后仍 200 且 `boss_summary` 等于静态模板 |
| TC-7 | 开启下周须用户主动确认（F-07-05） | PASS | 前端 `nextWeek` 显式传 `accept_suggestion: true`；后端 `start_next_week` 在 `accept_suggestion=False` 抛 422「须确认开启下一周」（`quest_service.py:296-297`） |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| API 路由与契约 | PASS | `quests.py:108-153` 三端点；响应字段对齐 `docs/api-contracts.md` review/next-week/pause |
| P07 原型文案对齐 | PASS | 与 `docs/prototypes/index.html:198-239` 一致：「本周 Boss 战 · 已完成」「完成小事件」「产出物」「本周你推进了」「成长资产」「下一周建议」「开启下一周副本」「暂停，下次再说」 |
| P07 路由守卫 | PASS | `/quest/review` 无 `QuestFlowGuard`（`router/index.tsx:43-46`），review 后 completed 仍可首屏加载（经 getActive 取 id 后调 review） |
| Vite 代理与 CORS | PASS | `vite.config.ts:17-29` `/api` + `/ws`；`frontend/.env` `VITE_API_BASE_URL=/api` |
| 密钥泄露 | PASS | 业务源码 / docs / `.sdd` 无 Key 明文；Key 仅存在于 `backend/.env`（配置预期位置） |
| 测试库隔离 | PASS | `test_review.py` 临时 SQLite + `dependency_overrides[get_db]`；无运行时库 drop_all |
| httpx trust_env | PASS | 业务层经 `LLMService` 封装，无裸 httpx 快捷调用 |

## LLM / Fallback 标注

| 项 | 状态 |
|----|------|
| LLM Key 配置 | **已配置**（`backend/.env` 含 A/B 双 Key 与 `LLM_NODE_QUEST_REVIEW_*`） |
| Agent 自动化 pytest | **Mock/fallback only**（沙箱网络受限，review 实际命中 `review_templates.build_static_review`，HTTP 200 非 503） |
| Fallback 路径证据 | patch `LLMService.chat_json` → `LLMError` 后 review 仍成功，`boss_summary` 为静态模板句 |
| 用户门禁真实 LLM | 待用户在 8003 端口、Key 可用环境下完成 Day7→P07，确认文案非静态模板（可选对比 `review_templates.REVIEW_BOSS_SUMMARY`） |

## 真实联调证据

### pytest TestClient（隔离库）

```
POST /quests/{id}/review（7 天完成后） → 200, quest.status=completed, review 字段齐全
POST /quests/{id}/review（未完成）     → 422
POST /quests/{id}/next-week            → 200, redirect=clarify, goal.status=active
POST /quests/{id}/pause                → 200, status=abandoned, GET /active data=null, goal paused
```

### uvicorn smoke（127.0.0.1:18099，短时启动后关闭）

```
POST /api/v1/quests/{fake-uuid}/review  → 404（路由可达）
GET  /api/v1/quests/active              → 200, data=null
```

## 用户门禁（user_gate）

任务标记 `user_gate: true`。Agent 侧代码、单测与静态/短时 API 验证已全部 PASS。

**待用户确认**（用户门禁端口 5175/8003）：

1. `frontend/.env.local` 设 `VITE_USE_MOCK=false`，`VITE_BACKEND_PROXY_TARGET=http://localhost:8003`
2. 启动后端 `8003`、前端 `5175`
3. 完成 Day7 反馈页 → 自动/点击进入 P07，确认 Boss 总结、统计、产出、观察、下周建议均展示
4. 点击「开启下一周副本」→ 进入 `/clarify`（P02），可继续澄清/生成新周副本
5. （新会话或另开分支）在 P07 点击「暂停，下次再说」→ 回 P01 目标输入；再次访问 `/` 不强制进 `/hub`
6. （可选）LLM 可用时对比复盘文案是否为 AI 生成（非静态模板句）

## 验证命令摘要

```bash
cd backend && PYTHONPATH=.. ../.venv/bin/python -m pytest tests/ -q          # 67 passed
cd frontend && npm run type-check && npm run lint && npm run build             # 通过
```

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | `flowStore.reviewQuestId` 未持久化，浏览器硬刷新 P07 时 getActive 已为 null，会跳回首页 | P07 / flowStore | 可纳入后续 UX 优化或 T-012 E2E 覆盖 sessionStorage 持久化 |
