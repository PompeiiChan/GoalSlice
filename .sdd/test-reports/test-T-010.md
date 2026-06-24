# 测试报告：T-010 进行中枢与成长资产功能闭环

**测试时间**：2026-06-25 01:21（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | 用户有进行中副本时访问首页，页面自动进入进行中枢（P08）而非目标输入页 | PASS | `guards.tsx:8-33` `HomeRouteGuard` 在 `VITE_USE_MOCK=false` 时调用 `questService.getActive()`，有活跃副本则 `<Navigate to="/hub">`；`router/index.tsx:18-23` 首页包裹该守卫 |
| AC-2 | 用户在进行中枢（P08）看到当前主线标题、通关条件、本周进度 x/7 与已积累成长资产列表 | PASS | `HubPage.tsx:73-94` 展示 `quest_title`、`success_condition`、环形进度 `{completed}/{total}`（默认 7）、`assetService.list` 聚合 `AssetTag` 墙 |
| AC-3 | 用户在 P08 点击「进入今日任务」，页面跳转到 P04 并展示当天任务 | PASS | `HubPage.tsx:85-87` `navigate('/quest/today')`；`QuestTodayPage.tsx:35-47` 调用 `eventService.getToday()` 加载当日任务 |
| AC-4 | 用户在 P08 点击「查看主线详情」，进入 P03 只读模式浏览 7 日计划（不可再次接受） | PASS | 原型文案为「查看完整主线 →」（`docs/prototypes/index.html:191`），实现一致；`HubPage.tsx:99` 跳转 `/quest/preview?readonly=1`；`QuestPreviewPage.tsx:65-85` 只读分支走 `getActive` + `getDetail`，`178-197` 隐藏接受/重新生成按钮 |
| AC-5 | 用户完成至少一次任务后，P08 成长资产列表展示对应资产名称标签 | PASS | `test_list_assets_by_quest` 完成 event 后 `GET /assets?quest_id=` 返回 `asset_name`；`HubPage.tsx:39-40,90-93` 按名称聚合展示 `AssetTag` |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `pytest backend/tests`（quests/active、quests/{id}、assets） | PASS | 全量 **63 passed**；`test_get_active_quest_with_progress`、`test_get_active_quest_null_when_none`、`test_get_quest_detail`、`test_list_assets_by_quest` 全绿 |
| TC-2 | `npm run type-check / lint / build` | PASS | type-check 0 error；lint 3 warnings（既有 react-refresh）；build 成功 |
| TC-3 | `VITE_USE_MOCK=false` 时 P08 命中 `GET /quests/active`、`GET /assets` | PASS | `questService.ts:62-68`、`assetService.ts:15-23` 非 Mock 分支调用真实 API；`HubPage.tsx:33-40` 加载链路 |
| TC-4 | P03 只读模式命中 `GET /quests/{quest_id}` | PASS | `QuestPreviewPage.tsx:66-68` readonly 时 `getDetail(active.quest.quest_id)` |
| TC-5 | 无活跃副本时 `GET /quests/active` 返回 `data=null`，前端回 P01 | PASS | `quests.py:85-86` 返回 `success_response(None)`；`test_get_active_quest_null_when_none` 断言 `data is None`；`guards.tsx:20-23` 无 active 不跳转；`HubPage.tsx:34-36` 无 data 时 `navigate('/')` |
| TC-6 | 页面无 `[Mock]` 残留 | PASS | `frontend/src` 全局 grep 无 `[Mock]` 字符串 |
| TC-7 | MVP 仅允许 1 个 in_progress quest 校验生效 | PASS | `quest_service.py:135-136` `has_in_progress_quest_for_session` 冲突抛 422；`test_accept_quest_conflict_when_already_in_progress` 第二次 accept 返回 422 |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| API 路由与契约 | PASS | `quests.py:80-99`、`assets.py:19-26`；字段对齐 `docs/api-contracts.md` |
| 路由守卫真实 API | PASS | `guards.tsx` 三处守卫非 Mock 均用 `questService.getActive()`，非 Mock 状态函数 |
| Vite 代理与 CORS | PASS | `vite.config.ts:17-29` `/api` + `/ws` 代理；`frontend/.env` `VITE_API_BASE_URL=/api`；`config.py:17-22` CORS 含 5199/5175 |
| 密钥泄露 | PASS | 业务源码无硬编码 Key；报告不复述 Key |
| 测试库隔离 | PASS | 各 test 模块使用临时 SQLite + `dependency_overrides[get_db]`；无运行时库 `drop_all` |
| ruff / mypy | PASS | `ruff check backend/src backend/tests` All checks passed；`mypy` Success 49 files |
| TODO/FIXME | PASS | T-010 相关 `backend/src`、`frontend/src` 无 TODO/FIXME/HACK（pycore 模板 TODO 不在范围） |

## 真实联调证据

### pytest TestClient（隔离库）

```
GET /api/v1/quests/active     → 200, data.quest + progress（有副本）
GET /api/v1/quests/active     → 200, data=null（无副本）
GET /api/v1/quests/{id}       → 200, days[7]
GET /api/v1/assets?quest_id=  → 200, items 含 asset_name（完成任务后）
POST /api/v1/quests（第二次）  → 422（单副本冲突）
```

### uvicorn smoke（127.0.0.1:18099，短时启动后关闭）

```
GET /api/v1/quests/active  X-Session-Id: tester-empty
→ {"code":200,"data":null,...}

GET /api/v1/assets  X-Session-Id: tester-empty
→ {"code":200,"data":{"items":[]},...}
```

注：8099 端口被其他进程占用，smoke 使用 18099 临时端口；不影响 PASS 判定。

## 用户门禁（user_gate）

任务标记 `user_gate: true`。Agent 侧代码、单测与静态/短时 API 验证已全部 PASS。

**待用户确认**（用户门禁端口 5175/8003）：

1. `frontend/.env.local` 设 `VITE_USE_MOCK=false`，`VITE_BACKEND_PROXY_TARGET=http://localhost:8003`
2. 启动后端 `8003`、前端 `5175`
3. **有活跃副本**：访问 `/` 应自动进入 `/hub`（P08），展示主线标题、通关条件、进度环 x/7、成长资产标签
4. 点击「进入今日任务」→ P04 展示当天任务
5. 点击「查看完整主线 →」→ P03 只读 7 日时间线，无「开始 Day 1」按钮
6. **无活跃副本**（新 session 或暂停后）：访问 `/` 停留 P01，访问 `/hub` 应重定向回 `/`

## 验证命令摘要

```bash
cd backend && PYTHONPATH=.. ../.venv/bin/python -m pytest tests/ -q          # 63 passed
../.venv/bin/python -m ruff check backend/src backend/tests                  # All checks passed
../.venv/bin/python -m mypy backend/src backend/tests                        # Success
cd frontend && npm run type-check && npm run lint && npm run build           # 通过（lint 3 warnings）
```
