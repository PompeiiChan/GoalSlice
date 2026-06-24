# GoalSlice 启动指南

本文说明如何在本地启动 GoalSlice 前后端，并完成 **Mock 演示** 与 **真实 API 联调** 两种模式。

---

## 1. 环境要求

| 依赖 | 版本 |
|------|------|
| Python | ≥ 3.11 |
| Node.js | ≥ 18 |
| npm | ≥ 9 |

项目根目录：`Projects_Repo/goalslice/`

Python 虚拟环境（已创建时跳过）：

```bash
cd Projects_Repo/goalslice
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" -e backend
.venv/bin/pip install greenlet
```

---

## 2. 端口说明

| 用途 | 前端端口 | 后端端口 | 说明 |
|------|----------|----------|------|
| **Agent 开发验证** | 5199 | 8099 | Cursor/Codex 自动化测试默认端口 |
| **用户门禁验收** | 5175 | 8003 | 手动浏览器全流程验收 |

前端通过 Vite 代理将 `/api` 转发到后端，浏览器只访问前端端口。

---

## 3. 后端配置与启动

### 3.1 配置 `backend/.env`

```bash
cp backend/.env.example backend/.env
```

必填项（真实 LLM 联调）：

```env
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3.5-27B
LLM_API_KEY_A=<你的 Key A>
LLM_API_KEY_B=<你的 Key B>
```

其他默认值（Agent 验证 8099）：

```env
APP_HOST=127.0.0.1
APP_PORT=8099
DATABASE_URL=sqlite+aiosqlite:///./data/goalslice.db
```

**用户门禁**时可将 `APP_PORT=8003`。

> Key 仅写入 `backend/.env`，勿提交到 Git，勿写入文档或测试报告。

### 3.2 启动后端

```bash
cd Projects_Repo/goalslice/backend
PYTHONPATH=.. ../.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8099 --reload
```

用户门禁端口：

```bash
PYTHONPATH=.. ../.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 --reload
```

验证：

```bash
curl http://127.0.0.1:8099/health
# 期望：{"code":200,"message":"success","data":{"status":"ok","version":"0.1.0"}}
```

应用启动时会自动执行 `init_db()` 与 SQLite 幂等迁移（`src/db/migrations.py`）。

---

## 4. 前端配置与启动

### 4.1 环境变量

主配置：`frontend/.env`

```env
VITE_API_BASE_URL=/api
VITE_BACKEND_PROXY_TARGET=http://localhost:8099
VITE_USE_MOCK=true
VITE_DEMO_RESET=true
```

| 变量 | 说明 |
|------|------|
| `VITE_API_BASE_URL` | 固定为 `/api`；axios 请求走 Vite 代理 |
| `VITE_BACKEND_PROXY_TARGET` | Vite 将 `/api` 代理到此地址（见 `vite.config.ts`） |
| `VITE_USE_MOCK` | `true` = 纯前端 Mock；`false` = 真实后端 API |
| `VITE_DEMO_RESET` | `true` 时顶栏显示「回到最开始」按钮 |

**真实 API 联调**（用户门禁）建议用 `frontend/.env.local` 覆盖，不改动团队默认 `.env`：

```env
VITE_USE_MOCK=false
VITE_BACKEND_PROXY_TARGET=http://localhost:8003
VITE_DEMO_RESET=true
```

### 4.2 Vite 代理

`frontend/vite.config.ts` 将 `/api` 代理到 `VITE_BACKEND_PROXY_TARGET`：

```ts
proxy: {
  '/api': { target: backendTarget, changeOrigin: true },
}
```

因此前端请求 `GET /api/v1/goals/active` 实际转发到 `http://localhost:<后端端口>/api/v1/goals/active`。

### 4.3 启动前端

Agent 验证（5199 → 8099）：

```bash
cd Projects_Repo/goalslice/frontend
npm install
npm run dev
# 默认 http://127.0.0.1:5199
```

用户门禁（5175 → 8003）：

```bash
VITE_BACKEND_PROXY_TARGET=http://localhost:8003 npm run dev -- --port 5175
```

---

## 5. Mock 与真实 API 切换

| 模式 | `VITE_USE_MOCK` | 数据存储 | 适用场景 |
|------|-----------------|----------|----------|
| Mock 演示 | `true` | `localStorage` | 无后端、原型走查 |
| 真实联调 | `false` | SQLite + 后端 | 功能验收、E2E |

切换后需**重启** Vite dev server。

---

## 6. 用户门禁全流程（5175 / 8003）

1. 后端 `8003` + 前端 `5175`，`VITE_USE_MOCK=false`
2. **P01** 输入目标 → **P02** 完成 5 题澄清 → **P03** 生成并接受计划
3. **P04** 完成每日任务 → **P05** 查看反馈（重复 7 天）
4. Day7 完成 → **P07** 周复盘 →「开启下一周副本」进入 **P02**
5. 可选：P04 降级、P08 中枢、暂停副本回 P01

有进行中副本时访问 `/` 会自动进入 **P08**。

---

## 7. LLM 不可用（503）行为

| 端点 | LLM 不可用时的行为 |
|------|-------------------|
| `POST /quests/generate` | **503**，前端 P03 展示友好错误 +「返回澄清页」 |
| `POST /events/{id}/downgrade` | **200**，静态降级方案 fallback |
| `POST /events/{id}/complete` | **200**，静态反馈模板 fallback |
| `POST /quests/{id}/review` | **200**，静态复盘模板 fallback |

测试 503：清空 `backend/.env` 中的 `LLM_API_KEY_A/B` 后重启后端，在 P03 点「重新生成计划」。

---

## 8. 质量门禁命令

### 后端

```bash
cd Projects_Repo/goalslice/backend
../.venv/bin/ruff check src tests
../.venv/bin/mypy src
PYTHONPATH=.. ../.venv/bin/python -m pytest tests/ -q
```

### 前端

```bash
cd Projects_Repo/goalslice/frontend
npm run type-check
npm run lint
npm run build
```

### E2E API 回归（跨模块全链路）

不启动浏览器，通过 TestClient 模拟完整 API 旅程：

```bash
cd Projects_Repo/goalslice/backend
PYTHONPATH=.. ../.venv/bin/python -m pytest tests/test_e2e.py -v
```

覆盖：主流程（P01→P07）、暂停分支、计划生成 503。

---

## 9. 常见问题

**`no such column` 联调报错**  
删除 `backend/data/goalslice.db` 后重启后端，或确认 `migrations.py` 已执行（`on_startup` 自动触发）。

**CORS / 跨域**  
开发环境走 Vite 代理，无需额外 CORS；直连后端端口时需在后端 `cors_origins` 包含前端端口。

**Session**  
前端 `api.ts` 自动携带 `X-Session-Id`（`localStorage`）；「回到最开始」会换新 session。

---

## 10. 目录速查

```
goalslice/
├── backend/          # FastAPI + SQLite
│   ├── .env          # LLM Key（本地，不提交）
│   └── src/
├── frontend/         # React + Vite
│   ├── .env          # Mock 默认配置
│   └── .env.local    # 本地联调覆盖（可选）
├── docs/startup.md   # 本文件
└── .sdd/tasks.json   # SDD 任务状态
```
