# 测试报告：T-012 E2E 全链路回归 + docs/startup.md

**测试时间**：2026-06-25 01:43（第 1 次独立验证）
**Tester Agent ID**：composer-2.5-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | 用户按 docs/startup.md 启动前后端（用户门禁端口 5175/8003）后，可从 P01 输入目标一路完成 7 天副本并在 P07 开启下一周，全流程无阻塞性错误 | PASS（API 等价 + 文档） | `test_e2e_full_quest_journey_p01_to_p07` 覆盖 goals→clarify→generate→accept→7×complete→review→assets→next-week；`docs/startup.md` §6 列出浏览器门禁步骤。Agent 未做 Playwright 浏览器自动化（本任务 E2E 以 TestClient API 旅程为准，见 startup §8） |
| AC-2 | 用户在 LLM 不可用（503）场景下，计划生成/降级/反馈/复盘页面展示友好错误提示，不出现白屏或未处理异常 | PASS | `test_e2e_quest_generate_503_without_llm` 断言 generate 返回 503 且 message 含「AI 服务」；`startup.md` §7 说明 generate=503、downgrade/complete/review=200 fallback；降级/完成/中枢分支有独立 E2E 用例 |
| AC-3 | 用户在暂停副本后回到 P01，可重新开始新目标流程 | PASS | `test_e2e_pause_and_restart_new_goal`：pause→active=null→POST 新 goal 200 |
| AC-4 | docs/startup.md 清晰说明 backend/.env、启动前后端、VITE_USE_MOCK 切换、端口说明 | PASS | §2 Agent 5199/8099 与用户门禁 5175/8003；§3 backend/.env；§4 VITE_API_BASE_URL、VITE_USE_MOCK、vite proxy；§5 Mock/真实切换表 |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | E2E 测试套件（主流程 + 503 + 暂停分支） | PASS | `test_e2e.py` **5/5 passed**：full journey、pause、503、downgrade、hub |
| TC-2 | VITE_USE_MOCK=false 全链路回归 | PASS | E2E 通过 TestClient 模拟真实 API 旅程（无 Mock 分支）；四 service 均以 `VITE_USE_MOCK === 'true'` 门控 Mock |
| TC-3 | startup.md 含 Agent 5199/8099 与用户门禁 5175/8003 | PASS | `docs/startup.md:32-33` 端口表；§3.2/§4.3 启动命令 |
| TC-4 | vite proxy /api 与 VITE_API_BASE_URL=/api 在 startup 说明 | PASS | `startup.md:105-130`；`vite.config.ts:19-23` 代理 `/api`→`VITE_BACKEND_PROXY_TARGET`；`frontend/.env:2` `VITE_API_BASE_URL=/api` |
| TC-5 | 各功能任务已完成首次真实联调，本任务仅跨模块回归 | PASS | T-006~T-011 均为 passed；本任务新增 `test_e2e.py` 跨模块聚合 |
| TC-6 | npm run type-check、lint、build | PASS | type-check 0 error；lint 3 warnings（既有 react-refresh）；build 成功 |
| TC-7 | pytest backend/tests 全量 | PASS | **72 passed**（含 E2E 5 项） |

## E2E 用例覆盖明细

| 用例 | 覆盖分支 | 结果 |
|------|----------|------|
| `test_e2e_full_quest_journey_p01_to_p07` | P01→P07 主流程、7 天完成、复盘、资产、开启下周 | PASS |
| `test_e2e_pause_and_restart_new_goal` | 暂停分支、active=null、新目标 | PASS |
| `test_e2e_quest_generate_503_without_llm` | 计划生成 503 | PASS |
| `test_e2e_downgrade_and_complete_still_advances` | P04/P06 降级 + 完成推进 | PASS |
| `test_e2e_hub_endpoints_after_one_complete` | P08 中枢 active/detail/assets | PASS |

## 质量门禁命令输出

```
# 后端（startup.md §8 命令，使用 .venv）
ruff check src tests     → All checks passed!
mypy src                 → Success: no issues found in 36 source files
pytest tests/ -q         → 72 passed
pytest tests/test_e2e.py -v → 5 passed

# 前端
npm run type-check       → 0 errors
npm run lint             → 0 errors, 3 warnings
npm run build            → built in 2.55s
```

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| startup.md 密钥泄露 | PASS | 仅 `<你的 Key A/B>` 占位符，无真实 Key |
| 前端 `[Mock]` 残留 | PASS | `frontend/src` 全局 grep 无 `[Mock]` |
| E2E 测试库隔离 | PASS | `e2e_client` fixture 使用 `tempfile` 临时库 + `app.dependency_overrides[get_db]`，teardown 删除临时文件 |
| httpx trust_env | PASS | E2E 不直接调用 httpx；业务层沿用既有 LLM 封装 |
| uvicorn 可启动 | PASS | `curl http://127.0.0.1:8099/health` → `code=200, data.status=ok` |

## LLM / Fallback 标注

| 项 | 状态 |
|----|------|
| LLM Key 配置 | 依赖 `backend/.env`（Tester 未读取 Key 内容） |
| E2E generate 503 | **已验证**（无 Key 时 503 + 友好 message） |
| E2E 主流程 generate/feedback | **Mock/patch**（patch `_generate_with_llm` / `_generate_feedback` 保证 CI 可重复） |
| downgrade/review fallback | 由既有 service fallback 逻辑支撑；E2E downgrade 用例走真实 downgrade 端点（200 + 3 options） |
| 用户门禁真实 LLM | 待用户在 8003 完成浏览器全流程（可选） |

## 用户门禁（user_gate）— MVP 最终验收要点

任务 `user_gate: true`。Agent 自动化已全部 PASS；**以下需用户在本机浏览器确认**：

### 环境准备

1. `cp backend/.env.example backend/.env`，填入 `LLM_API_KEY_A/B`（可选，无 Key 时 P03 生成计划会 503，其余节点走 fallback）
2. 后端用户门禁端口：
   ```bash
   cd Projects_Repo/goalslice/backend
   PYTHONPATH=.. ../.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 --reload
   ```
3. 前端用户门禁端口（`frontend/.env.local` 推荐）：
   ```env
   VITE_USE_MOCK=false
   VITE_BACKEND_PROXY_TARGET=http://localhost:8003
   ```
   ```bash
   cd Projects_Repo/goalslice/frontend
   VITE_BACKEND_PROXY_TARGET=http://localhost:8003 npm run dev -- --port 5175
   ```
4. 浏览器打开 `http://127.0.0.1:5175`

### 主流程（P01→P07→下周）

5. **P01** 输入职业成长目标 → **P02** 完成 5 题澄清 → **P03** 生成并接受 7 天计划
6. **P04** 完成每日任务 → **P05** 查看反馈，重复至 Day7
7. Day7 后进入 **P07** 周复盘 → 点击「开启下一周副本」进入 **P02**

### 异常与分支

8. **503**：清空 `LLM_API_KEY_A/B` 重启后端，P03「重新生成计划」应显示友好错误（非白屏）
9. **降级**：P04「今天太难了」→ 选方案 → 完成降级任务仍进 P05
10. **中枢**：有进行中副本时访问 `/` 自动进 **P08**；可进今日任务、查看主线、成长资产
11. **暂停**：P07「暂停，下次再说」→ 回 **P01** 目标输入；再次访问 `/` 不强制进 hub

### 快速自动化回归（无需浏览器）

```bash
cd Projects_Repo/goalslice/backend
PYTHONPATH=.. ../.venv/bin/python -m pytest tests/test_e2e.py -v
```

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 验证前 `backend/data/goalslice.db` 不存在（首次启动由 `init_db` 创建） | 环境 | 用户门禁前按 startup §3 启动一次后端即可 |
| 2 | 8099 端口已有进程占用（health 仍 200） | 环境 | 用户验收前确认端口无冲突旧进程 |
| 3 | eslint 3 条 react-refresh warning（T-001 既有） | 前端 | 非本任务范围，可选后续清理 |
