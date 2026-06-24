# 开发计划

> 设计阶段与开发阶段的衔接文件。所有开发进度以本文件为准。

## 一、功能清单总览

| 序号 | 功能编号 | 功能名称 | 一句话描述 | 对应页面 | 优先级 | 状态 |
|------|---------|---------|-----------|---------|--------|------|
| 1 | F-01-01 | 目标输入 | 自然语言输入职业成长目标 | P01 | MVP | 待开发 |
| 2 | F-01-02 | 示例目标快捷填入 | 点击 Chip 填入输入框 | P01 | MVP | 待开发 |
| 3 | F-01-03 | 进行中副本检测 | 有副本时展示继续入口 | P01 | MVP | 待开发 |
| 4 | F-02-01 | 逐题卡片澄清 | 5 题低摩擦问答（**Demo/MVP：静态题库与选项**） | P02 | MVP | 待开发 |
| 5 | F-03-01 | 生成一周主线 | AI 生成 7 天预览 | P03 | MVP | 待开发 |
| 6 | F-03-03 | 接受计划 | 创建副本开始 Day 1 | P03 | MVP | 待开发 |
| 7 | F-04-01 | 今日任务展示 | 每天一件事 | P04 | MVP | 待开发 |
| 8 | F-04-03 | 标记完成 | 触发意义反馈 | P04 | MVP | 待开发 |
| 9 | F-06-01 | 任务降级 | AI 生成更小版本 | P06 | MVP | 待开发 |
| 10 | F-05-01 | 完成反馈 | 意义解释 + 资产 + 进度 | P05 | MVP | 待开发 |
| 11 | F-08-01 | 副本状态概览 | 回访用户中枢 | P08 | MVP | 待开发 |
| 12 | F-07-01 | 周复盘 | Boss 总结 + 下周推荐 | P07 | MVP | 待开发 |
| 13 | F-07-05 | 开启下周 | 续关下一周副本 | P07 | MVP | 待开发 |

**延后（Demo 之后，见 PRD F-02-05）**：澄清题卡片选项由 AI 根据 `raw_goal` 针对性生成；Demo/MVP 与 Mock 阶段不实现，继续使用 `mocks/data.ts` 静态 `CLARIFY_QUESTIONS`。

## 二、数据契约摘要

完整数据契约见 `docs/PRD.md` 第 8 章。核心实体：

- `Goal` — 用户目标
- `UserContext` — 澄清上下文
- `Quest` — 一周副本
- `DailyEvent` — 每日小事件
- `GrowthAsset` — 成长资产

统一响应格式与接口字段以 `docs/api-contracts.md` 为唯一权威源。

## 二点五、外部服务与测试权限清单

| 服务 | 用途 | 配置项字段 | MVP 必需 | Tester 完整联调权限 | 缺失时策略 | 状态 |
|------|------|------------|----------|--------------------|------------|------|
| 硅基流动 LLM | 计划生成、降级、反馈、复盘 | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | 是 | 用户提供测试 Key + 可调用额度 | 前端 Mock JSON + 占位文案；后端返回 503 | **已确认：用户供 Key，模型千问三系列，型号联调前在 `.env` 配置** |
| Embedding / Rerank | 无 | — | 否 | — | 不适用 | 无 |
| 对象存储 | 无 | — | 否 | — | 文本存 DB | 无 |
| 登录 / OAuth | 无 | — | 否 | — | `X-Session-Id` | 无 |

真实 Key 只写入 `backend/.env`，不得提交仓库。

推荐 `.env` 示例：

```env
LLM_API_KEY_A=<硅基流动 Key A，计划生成+完成反馈主用>
LLM_API_KEY_B=<硅基流动 Key B，降级+复盘主用，互为兜底>
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen3.5-27B
```

双 Key 路由见 `backend/.env.example`。真实 Key 只写入 `backend/.env`，不得提交仓库。

## 三、前端开发清单

### 前端技术选型

| 层级 | 选择 | 说明 |
|------|------|------|
| 框架 | React 18 | 业务 SPA |
| 语言 | TypeScript | 全量类型化 |
| 构建 | Vite | 开发代理 `/api` → 8000 |
| 路由 | react-router v6 | 8 页 + 守卫 |
| 状态 | Zustand | session、quest |
| 请求 | Axios | `X-Session-Id` 拦截器 |
| 组件库 | Ant Design 5 | R1 珊瑚红 token 覆写 |
| 工程化 | ESLint + Prettier + tsc + build | 自动验收 |

| 序号 | 页面 | 路由 | 涉及功能 | Mock 数据来源 | 状态 |
|------|------|------|---------|--------------|------|
| P01 | 首页 | `/` | F-01-01~04 | `mocks/goals.ts` | 待开发 |
| P02 | 澄清 | `/clarify` | F-02-01~04 | `mocks/data.ts` → `CLARIFY_QUESTIONS`（**静态选项，非 LLM**） | 待开发 |
| P03 | 主线预览 | `/quest/preview` | F-03-01~05 | `mocks/quest.ts` | 待开发 |
| P04 | 每日任务 | `/quest/today` | F-04-01~06, F-06 | `mocks/events.ts` | 待开发 |
| P05 | 完成反馈 | `/quest/feedback` | F-05-01~05 | complete 响应 | 待开发 |
| P06 | 降级 Modal | P04 内嵌 | F-06-01~03 | downgrade 响应 | 待开发 |
| P07 | 周复盘 | `/quest/review` | F-07-01~06 | `mocks/review.ts` | 待开发 |
| P08 | 进行中枢 | `/hub` | F-08-01~04 | active quest | 待开发 |

### 前端共享组件

| 组件 | 原型参考 | 状态 |
|------|---------|------|
| AppHeader | `.header` | 待开发 |
| QuestCard | `.card--quest` | 待开发 |
| MeaningBlock | `.meaning-block` | 待开发 |
| CompleteHero | `.complete-hero` | 待开发 |
| DowngradeModal | `#modal-downgrade` | 待开发 |
| ProgressBar | `.progress-track` | 待开发 |
| AssetTag | `.tag-asset` | 待开发 |
| ClarifyOptionCard | `.option-card` | 待开发 |

### 前端自动验收标准

- [ ] 所有页面 UI 与 `docs/prototypes/` 一致（R1 色板）
- [ ] `VITE_USE_MOCK=true` 时可走通完整闭环
- [ ] Mock 数据结构与 `api-contracts.md` 一致
- [ ] 390px / 1280px 视口无溢出
- [ ] 全中文文案，示例含「提升 ×× 能力」规范

## 四、后端开发清单

| 序号 | 功能名称 | 依赖 | 对应接口 | 状态 |
|------|---------|------|---------|------|
| B00 | 基础设施 | 无 | `GET /health` | 待开发 |
| B01 | Session 中间件 | B00 | `X-Session-Id` 解析 | 待开发 |
| B02 | 数据模型与迁移 | B00 | — | 待开发 |
| B03 | 目标创建与澄清 | B02 | `POST /goals`, `PATCH /goals/{id}/clarify` | 待开发 |
| B04 | LLM 集成 | B00 | 硅基流动 Provider | 待开发 |
| B05 | 计划生成预览 | B03, B04 | `POST /quests/generate` | 待开发 |
| B06 | 接受计划创建副本 | B05 | `POST /quests` | 待开发 |
| B07 | 活跃副本查询 | B06 | `GET /quests/active`, `GET /quests/{id}` | 待开发 |
| B08 | 今日任务 | B06 | `GET /events/today` | 待开发 |
| B09 | 完成任务与反馈 | B04, B08 | `POST /events/{id}/complete` | 待开发 |
| B10 | 任务降级 | B04, B08 | `POST .../downgrade`, `PATCH .../apply-downgrade` | 待开发 |
| B11 | 周复盘 | B04, B06 | `POST /quests/{id}/review` | 待开发 |
| B12 | 下周与暂停 | B11 | `POST .../next-week`, `POST .../pause` | 待开发 |
| B13 | 成长资产 | B09 | `GET /assets` | 待开发 |

### 后端任务验收规则

- 基于 `pycore`：ConfigManager、APIServer、LLM Provider
- B00–B02 自动连续执行：`ruff` / 单元测试 / `GET /health` 200
- 业务任务须前后端真实联调：`VITE_USE_MOCK=false`
- LLM Key 缺失时：接口返回 503 或走 Mock Service，须在测试报告标注

## 五、功能详情（开发时逐个展开）

开发阶段由 Planner 产出 `.sdd/tasks.json`，Developer / Tester 按任务验收。每个业务任务闭环包含：

1. 后端 API 实现 + 单测
2. 前端 service 切真实 API
3. 页面联调
4. Tester 验收报告

## 六、开发顺序建议

### 阶段 1：前端 MVP（Mock，用户验收 UI/UX）

1. 工程初始化：`frontend/` Vite + React + TS + Ant Design
2. 设计 token 注入（R1 珊瑚红）
3. 按 P01 → P08 顺序实现页面 + Mock
4. **用户门禁**：确认布局、配色、交互与原型一致

### 阶段 2：后端基础设施（自动连续）

1. `backend/app` 目录 + PyCore 脚手架
2. SQLAlchemy 模型（5 实体）
3. `GET /health`、Session 中间件
4. **Agent 自动验收**

### 阶段 3：逐功能闭环

1. 目标 + 澄清（B03）→ P01/P02 联调
2. 计划生成 + 接受（B05–B06）→ P03 联调
3. 今日任务 + 完成反馈（B08–B09）→ P04/P05 联调
4. 降级（B10）→ P06 联调
5. 中枢 + 资产（B07, B13）→ P08 联调
6. 复盘 + 续关（B11–B12）→ P07 联调

### 阶段 4：E2E 回归

1. 完整路径：输入目标 → 7 天闭环 → 开启下周
2. 异常路径：降级、暂停、LLM 503
3. **用户门禁**：全流程无阻塞 Bug

## 七、设计产物索引

| 文件 | 路径 |
|------|------|
| PRD 定稿 | `docs/PRD.md` |
| 接口契约 | `docs/api-contracts.md` |
| 交互原型 | `docs/prototypes/index.html` |
| 视觉调研 | `.sdd/tmp/visual-research.md` |
