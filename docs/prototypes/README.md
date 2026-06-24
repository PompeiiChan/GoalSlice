# GoalSlice 就这 — B2 原型交接说明

> 原型仅供设计验证，**非生产前端源码**。生产实现须按 React + TypeScript + Vite + Ant Design 重建。

## 文件结构

```text
docs/prototypes/
├── index.html          # 可点击流程演示（主入口）
├── overview.html       # 全页面平铺预览
├── README.md           # 本文件
└── assets/
    ├── styles.css      # R1 珊瑚红设计 token
    └── app.js          # 最小状态机（非生产）
```

## 打开方式

```bash
# 在项目目录下用任意静态服务器打开，或直接双击 index.html
open docs/prototypes/index.html

# 演示回访用户落地页（直接进 P08 中枢）
open "docs/prototypes/index.html?hub=1"
```

## 页面清单

| 页面 ID | 名称 | 原型 screen id |
|---------|------|----------------|
| P01 | 首页（目标输入） | `home` |
| P02 | 目标澄清 | `clarify` |
| P03 | 本周主线预览 | `preview` |
| P04 | 每日任务 | `daily` |
| P05 | 完成反馈 | `feedback` |
| P06 | 任务降级 | Modal `#modal-downgrade` |
| P07 | 周复盘 | `review` |
| P08 | 进行中枢 | `hub` |

## 关键用户路径（已验证）

1. **新用户闭环**：首页 → 输入目标 → 澄清 5 题 → 预览计划 → 开始 Day 1 → 每日任务 → 完成 → 反馈 → 中枢
2. **降级路径**：每日任务 → 「太难了」→ 选降级方案 → 任务缩小 → 完成
3. **回访路径**：首页「继续本周」或 `?hub=1` → 中枢 → 进入今日任务
4. **周复盘路径**：反馈页（Day 7 模拟需手动改 state）→ 复盘 → 开启下周

## 关键组件清单

| 组件 | CSS 类 / 元素 | 生产须实现 |
|------|--------------|-----------|
| AppHeader | `.header` | 是，含进度 x/7 |
| Logo | `.logo`, `.logo-mark` | 是，最终替换品牌资产 |
| 主 CTA | `.btn-primary` | 是 |
| 澄清选项卡 | `.option-card` | 是 |
| Quest 主卡 | `.card--quest` | 是 |
| 意义说明块 | `.meaning-block` | 是，签名细节之一 |
| 完成反馈环 | `.check-ring` | 是，P05 质感锚点 |
| 进度条 | `.progress-track` | 是 |
| 成长资产 Tag | `.tag-asset` | 是 |
| Boss 卡 | `.card--boss` | 是 |
| 降级 Modal | `.modal-overlay` | 是 |
| 7 日时间轴 | `.timeline` | 是 |

## 交互状态

| 状态 | 原型覆盖 |
|------|---------|
| 默认 | 全部页面 |
| Hover | 按钮、选项卡、Chip |
| Disabled | 开始按钮（空输入）、澄清下一题（未选） |
| Selected | 澄清选项、降级方案 |
| Modal 开/关 | P06 |
| 完成庆祝 | P05 浅红底 + 红环黑勾 |

未覆盖（生产须补）：Loading（AI 生成中）、Error（LLM 失败）、Empty（无活跃副本）

## Mock 数据结构

```typescript
// 与 PRD 数据契约对齐的简化 Mock
interface Goal {
  raw_goal: string;
  goal_type: string;
  refined_goal: string;
}

interface UserContext {
  goal_type: string;
  weekly_outcome: string;
  available_time: string;
  current_level: string;
  failure_reason: string;
}

interface Quest {
  quest_title: string;
  success_condition: string;
  days: Array<{ day_index: number; title: string; estimated_time: string; boss?: boolean }>;
}

interface DailyEvent {
  day_index: number;
  event_title: string;
  event_description: string;
  meaning: string;
  status: "pending" | "completed" | "downgraded";
}
```

## 需要真实 API 的位置

| 功能 | API（见 PRD） | 原型处理 |
|------|--------------|---------|
| 生成一周计划 | `POST /api/v1/quests/generate` | 硬编码 WEEK_PLAN |
| 接受计划 | `POST /api/v1/quests` | 本地 state |
| 今日任务 | `GET /api/v1/events/today` | 硬编码 DAILY_TASK |
| 完成任务 | `POST /api/v1/events/{id}/complete` | 本地 state |
| 降级 | `POST .../downgrade` | 切换 downgraded 文案 |
| 周复盘 | `POST .../review` | 硬编码 P07 内容 |
| 会话 | `X-Session-Id` | 无，纯前端 state |

## 生产必须实现的视觉效果

- R1 色板：`#E8463A` Primary、`#FFF0EE` Soft、`#F5F5F7` Background
- P05 完成反馈：珊瑚红环 + 白勾 + 浅红庆祝区（签名锚点）
- 红色克制原则：不全屏铺红，红仅用于 CTA / 进度 / Day 标签 / Boss
- 单栏 640px 居中布局
- 每日页只展示一个 Quest 主卡

## 仅为原型展示的效果

- `alert()` 重新生成计划
- 周复盘需改 JS state 才能从 Day 7 自然进入（演示可直接访问 review screen）
- Logo 几何占位非最终品牌
- 进度环 SVG 为静态比例

## 设计参考

- Design Spec：`.sdd/tmp/ui-design-spec.md`（B2 完成后可删，内容已体现在 CSS）
- Visual Research：`.sdd/tmp/visual-research.md`
- 色板：方案 R1 · Doable 进化版 · 珊瑚红 + 完成勾
