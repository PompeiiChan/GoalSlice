# 接口契约

> 前端 Mock 和后端实现的唯一对齐依据。任何变更必须同步更新本文件。

## 通用约定

### Base URL

- 开发环境：`http://localhost:8000`
- 前端通过 Vite proxy 转发 `/api` → 后端

### 请求头

| Header | 必填 | 说明 |
|--------|------|------|
| `Content-Type` | 是（有 body 时） | `application/json` |
| `X-Session-Id` | 是（业务接口） | 匿名会话 UUID，前端首次访问生成并持久化 |

### 统一响应格式

**成功：**

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**错误：**

```json
{
  "code": 400,
  "message": "参数错误描述",
  "data": null
}
```

**分页（V2 预留）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### HTTP 状态码

| HTTP | code 字段 | 场景 |
|------|-----------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 参数校验失败 |
| 404 | 404 | 资源不存在 |
| 422 | 422 | 业务规则拒绝（如非 MVP 目标） |
| 500 | 500 | 服务器内部错误 |
| 503 | 503 | LLM 服务不可用 |

### 枚举定义

**goal_type：** `career_switch` | `skill_up` | `interview_prep` | `portfolio` | `expression` | `promotion` | `personal_brand` | `other`

**goal_status：** `active` | `completed` | `paused`

**quest_status：** `in_progress` | `completed` | `abandoned`

**event_status：** `pending` | `in_progress` | `completed` | `downgraded`

**output_type：** `text` | `checkbox`

**asset_type：** `ability_fragment` | `work_draft` | `interview_story` | `case_note` | `template_fragment` | `other`

**available_time：** `5m` | `15m` | `30m` | `60m_plus` | `flexible`

---

## 公共数据结构

### Goal

```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session-uuid",
  "raw_goal": "我想提升自己的会议总结能力",
  "goal_type": "skill_up",
  "refined_goal": "提升会议总结能力",
  "weekly_outcome": "完成一个具体产物",
  "status": "active",
  "created_at": "2026-06-24T10:00:00Z",
  "updated_at": "2026-06-24T10:05:00Z"
}
```

### UserContext

```json
{
  "session_id": "session-uuid",
  "goal_type": "skill_up",
  "weekly_outcome": "完成一个具体产物",
  "available_time": "15m",
  "current_level": "有一点了解，但不系统",
  "failure_reason": "不知道第一步做什么",
  "preferred_intensity": "low",
  "notes": ""
}
```

### QuestPreviewDay

```json
{
  "day_index": 1,
  "event_title": "列出最近 3 场会，标出最难总结的一场",
  "event_description": "回忆本周参加过的会议，写下名称并标出最难总结的一场。",
  "estimated_time": "15 分钟",
  "meaning": "先定位难点，后续练习才有的放矢。",
  "output_type": "text",
  "is_boss": false
}
```

### Quest

```json
{
  "quest_id": "660e8400-e29b-41d4-a716-446655440001",
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
  "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
  "total_days": 7,
  "current_day": 3,
  "status": "in_progress",
  "created_at": "2026-06-24T10:10:00Z",
  "updated_at": "2026-06-24T12:00:00Z"
}
```

### DailyEvent

```json
{
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "quest_id": "660e8400-e29b-41d4-a716-446655440001",
  "day_index": 3,
  "event_title": "用四格模板填空总结一场会",
  "event_description": "按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。",
  "estimated_time": "15 分钟",
  "meaning": "四格模板把模糊感受变成固定结构。",
  "output_type": "text",
  "output_hint": null,
  "user_output": null,
  "status": "in_progress",
  "original_event_id": null,
  "completed_at": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| output_hint | string \| null | 否 | 任务操作区输入框引导占位；`null` 时前端使用普适默认文案；联调后由 LLM 按当日任务生成 |

### GrowthAsset

```json
{
  "asset_id": "880e8400-e29b-41d4-a716-446655440003",
  "session_id": "session-uuid",
  "quest_id": "660e8400-e29b-41d4-a716-446655440001",
  "event_id": "770e8400-e29b-41d4-a716-446655440002",
  "asset_type": "template_fragment",
  "asset_name": "总结模板碎片",
  "asset_content": null,
  "created_at": "2026-06-24T12:30:00Z"
}
```

### DowngradeOption

```json
{
  "option_id": "5min",
  "title": "5 分钟版",
  "description": "写下一场会的名字 + 1 个结论，两句话就够。",
  "estimated_time": "5 分钟"
}
```

---

## 接口清单

### GET /health

**说明：** 健康检查，无需 `X-Session-Id`。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "version": "0.1.0"
  }
}
```

---

### POST /api/v1/goals

**说明：** 创建目标，进入澄清流程。若已有 `active` 目标且存在 `in_progress` 副本，返回 422。

> **Demo / MVP**：`clarify_questions` 为**静态默认题库**（5 题 + 固定 `options`），与原型一致；**不**调用 LLM 生成题目或选项。  
> **V1.2+（F-02-05）**：可根据 `raw_goal` 由 LLM **针对性生成**每题的 `options`（题干可保持 5 题骨架）；失败时降级为静态题库。字段结构不变。

**请求体：**

```json
{
  "raw_goal": "我想提升自己的会议总结能力"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| raw_goal | string | 是 | 1–500 字 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "goal": {
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "session-uuid",
      "raw_goal": "我想提升自己的会议总结能力",
      "goal_type": "skill_up",
      "refined_goal": null,
      "weekly_outcome": null,
      "status": "active",
      "created_at": "2026-06-24T10:00:00Z",
      "updated_at": "2026-06-24T10:00:00Z"
    },
    "clarify_questions": [
      {
        "question_id": "goal_type",
        "question": "这个目标更接近哪一类？",
        "options": ["转行 / 求职", "技能提升", "面试准备", "作品集建设", "个人品牌", "其他"]
      }
    ]
  }
}
```

**响应（失败 400）：**

```json
{
  "code": 400,
  "message": "raw_goal 不能为空",
  "data": null
}
```

**响应（失败 422）：**

```json
{
  "code": 422,
  "message": "已有进行中的副本，请先完成或暂停",
  "data": null
}
```

---

### PATCH /api/v1/goals/{goal_id}/clarify

**说明：** 提交澄清答案（可分批或一次提交全部）。

**路径参数：** `goal_id` (uuid)

**请求体：**

```json
{
  "answers": {
    "goal_type": "技能提升",
    "weekly_outcome": "完成一个具体产物",
    "available_time": "15 分钟",
    "current_level": "有一点了解，但不系统",
    "failure_reason": "不知道第一步做什么"
  },
  "notes": "可选补充"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "goal": {
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "session-uuid",
      "raw_goal": "我想提升自己的会议总结能力",
      "goal_type": "skill_up",
      "refined_goal": "提升会议总结能力",
      "weekly_outcome": "完成一个具体产物",
      "status": "active",
      "created_at": "2026-06-24T10:00:00Z",
      "updated_at": "2026-06-24T10:05:00Z"
    },
    "context": {
      "session_id": "session-uuid",
      "goal_type": "skill_up",
      "weekly_outcome": "完成一个具体产物",
      "available_time": "15m",
      "current_level": "有一点了解，但不系统",
      "failure_reason": "不知道第一步做什么",
      "preferred_intensity": "low",
      "notes": ""
    }
  }
}
```

**响应（失败 404）：**

```json
{
  "code": 404,
  "message": "目标不存在",
  "data": null
}
```

---

### POST /api/v1/quests/generate

**说明：** 基于目标与上下文生成 7 天计划预览（不持久化，须用户接受后才创建副本）。

**请求体：**

```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "preview": {
      "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
      "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
      "total_estimated_time": "每天约 15–30 分钟，共 7 天",
      "days": [
        {
          "day_index": 1,
          "event_title": "列出最近 3 场会，标出最难总结的一场",
          "event_description": "回忆本周参加过的会议，写下名称并标出最难总结的一场。",
          "estimated_time": "15 分钟",
          "meaning": "先定位难点，后续练习才有的放矢。",
          "output_type": "text",
          "is_boss": false
        },
        {
          "day_index": 7,
          "event_title": "Boss 战：独立完成一场真实会议的总结稿",
          "event_description": "选一场真实会议，产出完整总结稿。",
          "estimated_time": "30 分钟",
          "meaning": "本周成果沉淀。",
          "output_type": "text",
          "is_boss": true
        }
      ]
    }
  }
}
```

**响应（失败 422）：**

```json
{
  "code": 422,
  "message": "该目标暂不在 MVP 支持范围内，建议聚焦职业成长与技能提升",
  "data": null
}
```

**响应（失败 503）：**

```json
{
  "code": 503,
  "message": "AI 服务暂时不可用，请稍后重试",
  "data": null
}
```

---

### POST /api/v1/quests

**说明：** 用户接受计划，创建副本及 7 个 DailyEvent。

**请求体：**

```json
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "preview": {
    "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
    "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
    "days": []
  }
}
```

> `preview.days` 须与 generate 返回一致；后端可校验或忽略客户端传入、使用服务端缓存的 preview。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "quest": {
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
      "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
      "total_days": 7,
      "current_day": 1,
      "status": "in_progress",
      "created_at": "2026-06-24T10:10:00Z",
      "updated_at": "2026-06-24T10:10:00Z"
    },
    "today_event": {
      "event_id": "770e8400-e29b-41d4-a716-446655440010",
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "day_index": 1,
      "event_title": "列出最近 3 场会，标出最难总结的一场",
      "event_description": "回忆本周参加过的会议，写下名称并标出最难总结的一场。",
      "estimated_time": "15 分钟",
      "meaning": "先定位难点，后续练习才有的放矢。",
      "output_type": "text",
      "user_output": null,
      "status": "in_progress",
      "original_event_id": null,
      "completed_at": null
    }
  }
}
```

---

### GET /api/v1/quests/active

**说明：** 获取当前 session 下进行中的副本；无则 `data` 为 `null`。

**响应（成功 200，有副本）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "quest": {
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
      "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
      "total_days": 7,
      "current_day": 3,
      "status": "in_progress",
      "created_at": "2026-06-24T10:10:00Z",
      "updated_at": "2026-06-24T12:00:00Z"
    },
    "progress": {
      "completed_days": 2,
      "total_days": 7
    },
    "assets_count": 2
  }
}
```

**响应（成功 200，无副本）：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

### GET /api/v1/events/today

**说明：** 获取当前活跃副本的今日任务（`current_day` 对应事件）。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "event": {
      "event_id": "770e8400-e29b-41d4-a716-446655440002",
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "day_index": 3,
      "event_title": "用四格模板填空总结一场会",
      "event_description": "按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。",
      "estimated_time": "15 分钟",
      "meaning": "四格模板把模糊感受变成固定结构。",
      "output_type": "text",
      "user_output": null,
      "status": "in_progress",
      "original_event_id": null,
      "completed_at": null
    },
    "quest_summary": {
      "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
      "current_day": 3,
      "total_days": 7
    }
  }
}
```

**响应（失败 404）：**

```json
{
  "code": 404,
  "message": "没有进行中的副本或今日任务",
  "data": null
}
```

---

### POST /api/v1/events/{event_id}/complete

**说明：** 标记今日任务完成，返回意义反馈与成长资产。

**路径参数：** `event_id` (uuid)

**请求体：**

```json
{
  "user_output": "背景：周会同步项目进度…"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_output | string | 否 | 用户产出，`output_type=text` 时可选 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "event": {
      "event_id": "770e8400-e29b-41d4-a716-446655440002",
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "day_index": 3,
      "event_title": "用四格模板填空总结一场会",
      "event_description": "按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。",
      "estimated_time": "15 分钟",
      "meaning": "四格模板把模糊感受变成固定结构。",
      "output_type": "text",
      "user_output": "背景：周会同步项目进度…",
      "status": "completed",
      "original_event_id": null,
      "completed_at": "2026-06-24T12:30:00Z"
    },
    "feedback": {
      "completion_title": "Day 3 已完成",
      "action_label": "四格模板练习",
      "meaning_text": "你第一次把「我想提升会议总结能力」从模糊感受，变成了可重复使用的结构。",
      "asset": {
        "asset_id": "880e8400-e29b-41d4-a716-446655440003",
        "asset_type": "template_fragment",
        "asset_name": "总结模板碎片"
      },
      "progress": {
        "completed_days": 3,
        "total_days": 7
      },
      "tomorrow_preview": {
        "day_index": 4,
        "event_title": "找一份好纪要范例，标出 2 个可学习的写法"
      },
      "is_quest_completed": false
    }
  }
}
```

---

### POST /api/v1/events/{event_id}/downgrade

**说明：** 请求 AI 生成降级方案列表。

**路径参数：** `event_id` (uuid)

**请求体：**

```json
{
  "reason": "今天太难了"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "options": [
      {
        "option_id": "5min",
        "title": "5 分钟版",
        "description": "写下一场会的名字 + 1 个结论，两句话就够。",
        "estimated_time": "5 分钟"
      },
      {
        "option_id": "step1",
        "title": "只做第一步",
        "description": "只填四格模板里的「决议」一格。",
        "estimated_time": "5 分钟"
      },
      {
        "option_id": "tomorrow",
        "title": "明天继续",
        "description": "今天先休息，明天从原任务继续。",
        "estimated_time": "0 分钟"
      }
    ]
  }
}
```

---

### PATCH /api/v1/events/{event_id}/apply-downgrade

**说明：** 采用选中的降级方案，替换当日任务。

**路径参数：** `event_id` (uuid)

**请求体：**

```json
{
  "option_id": "5min"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "event": {
      "event_id": "770e8400-e29b-41d4-a716-446655440099",
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "day_index": 3,
      "event_title": "5 分钟版：写下一场会的名字 + 1 个结论",
      "event_description": "回忆最近一场会，写下会议名称和一个结论。",
      "estimated_time": "5 分钟",
      "meaning": "今天先完成「开始记录」比「完美纪要」更重要。",
      "output_type": "checkbox",
      "user_output": null,
      "status": "in_progress",
      "original_event_id": "770e8400-e29b-41d4-a716-446655440002",
      "completed_at": null
    }
  }
}
```

---

### POST /api/v1/quests/{quest_id}/review

**说明：** Day 7 完成后生成周复盘（quest 须 `in_progress` 且 current_day=7 当日已完成）。

**路径参数：** `quest_id` (uuid)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "review": {
      "completed_count": 5,
      "total_days": 7,
      "outputs": [
        "列出 3 场难总结的会议场景",
        "完成一次四格模板填空练习"
      ],
      "assets": [
        {
          "asset_id": "880e8400-e29b-41d4-a716-446655440003",
          "asset_type": "template_fragment",
          "asset_name": "总结模板碎片"
        }
      ],
      "observations": [
        "你在填空和拆解类任务上完成度高，写完整段落时容易拖延。"
      ],
      "boss_summary": "你不再只是「想写好纪要」，而是有了一份能直接用的总结方法",
      "next_week_suggestion": {
        "quest_title": "进入「文档写作副本」",
        "description": "把会议总结能力延伸到日常文档输出，练一份结构清晰的工作说明"
      }
    },
    "quest": {
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "completed",
      "current_day": 7
    }
  }
}
```

---

### POST /api/v1/quests/{quest_id}/next-week

**说明：** 用户确认开启下一周，创建新 goal 上下文或复用并进入澄清/生成流程。

**路径参数：** `quest_id` (uuid)

**请求体：**

```json
{
  "accept_suggestion": true
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "goal_id": "550e8400-e29b-41d4-a716-446655440000",
    "redirect": "clarify",
    "message": "已准备好进入下一周副本"
  }
}
```

---

### POST /api/v1/quests/{quest_id}/pause

**说明：** 暂停当前目标线，副本标记 `abandoned`，goal 标记 `paused`。

**路径参数：** `quest_id` (uuid)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "quest_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "abandoned"
  }
}
```

---

### GET /api/v1/assets

**说明：** 获取当前 session 的成长资产列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| quest_id | uuid | 否 | 按副本筛选 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "asset_id": "880e8400-e29b-41d4-a716-446655440003",
        "session_id": "session-uuid",
        "quest_id": "660e8400-e29b-41d4-a716-446655440001",
        "event_id": "770e8400-e29b-41d4-a716-446655440002",
        "asset_type": "template_fragment",
        "asset_name": "总结模板碎片",
        "asset_content": null,
        "created_at": "2026-06-24T12:30:00Z"
      }
    ]
  }
}
```

---

### GET /api/v1/quests/{quest_id}

**说明：** 获取副本详情含 7 日事件列表（P03 只读、P08 查看主线）。

**路径参数：** `quest_id` (uuid)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "quest": {
      "quest_id": "660e8400-e29b-41d4-a716-446655440001",
      "goal_id": "550e8400-e29b-41d4-a716-446655440000",
      "quest_title": "从「会议听完就忘」到「能写出可执行的会议总结」",
      "success_condition": "完成一份真实会议的总结稿（含背景、决议、待办）",
      "total_days": 7,
      "current_day": 3,
      "status": "in_progress",
      "created_at": "2026-06-24T10:10:00Z",
      "updated_at": "2026-06-24T12:00:00Z"
    },
    "days": [
      {
        "day_index": 1,
        "event_title": "列出最近 3 场会，标出最难总结的一场",
        "estimated_time": "15 分钟",
        "status": "completed",
        "is_boss": false
      },
      {
        "day_index": 7,
        "event_title": "Boss 战：独立完成一场真实会议的总结稿",
        "estimated_time": "30 分钟",
        "status": "pending",
        "is_boss": true
      }
    ]
  }
}
```
