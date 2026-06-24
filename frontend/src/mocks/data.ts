import type { QuestPreview, QuestPreviewDay } from '@/types/quest'
import { CLARIFY_QUESTIONS } from '@/constants/clarifyQuestions'

export { CLARIFY_QUESTIONS }

/** 演示主线：提升会议总结能力 — 对齐原型 DEMO_SCENARIO */
export const DEMO_RAW_GOAL = '我想提升自己的会议总结能力'
export const DEMO_HEADER_SHORT = '练就会议总结力'
export const DEMO_QUEST_TITLE = '从「会议听完就忘」到「能写出可执行的会议总结」'
export const DEMO_SUCCESS_CONDITION = '完成一份真实会议的总结稿（含背景、决议、待办）'
export const DEMO_TOTAL_ESTIMATED = '每天约 15–30 分钟，共 7 天'

/** P04 文本任务输入框默认引导（Demo/MVP 普适）；联调后优先使用 DailyEvent.output_hint（AI 生成） */
export const DEFAULT_TASK_OUTPUT_HINT =
  '写下或贴上你今天完成的内容，可以是要点、草稿或一段文字，不必追求完美。'

export const EXAMPLE_CHIPS = [
  { label: '转行到新行业', goal: '我想转行到一个新行业，但不知道从哪入手' },
  { label: '准备面试', goal: '我想系统准备接下来的面试' },
  { label: '提升复盘能力', goal: '我想提升自己的复盘能力' },
  { label: '提升文档写作能力', goal: '我想提升自己的文档写作能力' },
  { label: '提升会议总结能力', goal: DEMO_RAW_GOAL },
] as const

const WEEK_PLAN_DAYS: QuestPreviewDay[] = [
  {
    day_index: 1,
    event_title: '列出最近 3 场会，标出最难总结的一场',
    event_description: '回忆本周参加过的会议，写下名称并标出最难总结的一场。',
    estimated_time: '15 分钟',
    meaning: '先定位难点，后续练习才有的放矢。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 2,
    event_title: '读一份旧纪要，圈出缺失的 3 个关键信息',
    event_description: '找一份你写过的或收到的会议纪要，圈出缺失的背景、决议或待办。',
    estimated_time: '15 分钟',
    meaning: '知道「缺什么」比盲目重写更有针对性。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 3,
    event_title: '用「背景-讨论-决议-待办」四格模板，填空总结一场会',
    event_description:
      '选一场你最近参加的会，按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。不用完美，先填满。',
    estimated_time: '15 分钟',
    meaning:
      '会议总结难，往往难在不知道从何写起。四格模板把模糊感受变成固定结构，你先求「写完」，再求「写好」。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 4,
    event_title: '找一份好纪要范例，标出 2 个可学习的写法',
    event_description: '找一份你觉得写得好的会议纪要，标出 2 个值得学习的写法或结构。',
    estimated_time: '20 分钟',
    meaning: '从范例中学习比从零摸索更快建立标准。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 5,
    event_title: '用 5 句话写出一场会的核心结论',
    event_description: '选一场会，用 5 句话概括背景、讨论要点、决议和待办。',
    estimated_time: '15 分钟',
    meaning: '精炼表达是完整纪要的必经之路。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 6,
    event_title: '整理成你的专属会议总结模板',
    event_description: '把本周练习过的结构整理成一份可复用的会议总结模板。',
    estimated_time: '25 分钟',
    meaning: '模板化让每次会议都有固定抓手。',
    output_type: 'text',
    is_boss: false,
  },
  {
    day_index: 7,
    event_title: 'Boss 战：独立完成一场真实会议的总结稿',
    event_description: '选一场真实会议，产出完整总结稿（含背景、决议、待办）。',
    estimated_time: '30 分钟',
    meaning: '本周成果沉淀。',
    output_type: 'text',
    is_boss: true,
  },
]

export const DAILY_EVENT_TITLE_OVERRIDE: Record<number, string> = {
  3: '用四格模板填空总结一场会',
}

export function buildQuestPreview(): QuestPreview {
  return {
    quest_title: DEMO_QUEST_TITLE,
    success_condition: DEMO_SUCCESS_CONDITION,
    total_estimated_time: DEMO_TOTAL_ESTIMATED,
    days: WEEK_PLAN_DAYS,
  }
}

/** 每日完成反馈文案 — 按 day_index */
export const DAY_FEEDBACK: Record<
  number,
  {
    action_label: string
    meaning_text: string
    asset_name: string
    asset_type: 'template_fragment' | 'ability_fragment' | 'case_note'
  }
> = {
  1: {
    action_label: '会议场景梳理',
    meaning_text:
      '你不再只是「想写好纪要」，而是先锁定了最难总结的场景。知道难点在哪，练习才有方向。',
    asset_name: '总结场景卡',
    asset_type: 'ability_fragment',
  },
  2: {
    action_label: '缺失信息识别',
    meaning_text: '你开始用「缺什么」的视角审视纪要，这比盲目重写更有针对性。',
    asset_name: '总结场景卡',
    asset_type: 'ability_fragment',
  },
  3: {
    action_label: '四格模板练习',
    meaning_text:
      '你第一次把「我想提升会议总结能力」从模糊感受，变成了可重复使用的结构。以后每场会都有抓手，而不是听完就散。',
    asset_name: '总结模板碎片',
    asset_type: 'template_fragment',
  },
  4: {
    action_label: '范例拆解',
    meaning_text: '你从优秀范例中提炼了可学习的写法，这比从零摸索更快建立标准。',
    asset_name: '总结范例',
    asset_type: 'case_note',
  },
  5: {
    action_label: '核心结论提炼',
    meaning_text: '你用 5 句话概括了一场会的要点，精炼表达是完整纪要的必经之路。',
    asset_name: '总结模板碎片',
    asset_type: 'template_fragment',
  },
  6: {
    action_label: '专属模板整理',
    meaning_text: '你把本周练习过的结构整理成了可复用模板，以后每场会都有固定抓手。',
    asset_name: '总结模板碎片',
    asset_type: 'template_fragment',
  },
  7: {
    action_label: 'Boss 战总结稿',
    meaning_text:
      '你完成了本周 Boss 战——一份真实会议的完整总结稿。你不再只是「想写好纪要」，而是有了一份能直接用的总结方法。',
    asset_name: '总结范例',
    asset_type: 'case_note',
  },
}

export const REVIEW_OUTPUTS = [
  '列出 3 场难总结的会议场景',
  '找出旧纪要里缺失的关键信息',
  '完成一次四格模板填空练习',
  '拆解一份优秀纪要范例',
  '写出一场会的 5 句核心结论',
]

export const REVIEW_OBSERVATION =
  '你在填空和拆解类任务上完成度高，写完整段落时容易拖延。'

export const REVIEW_BOSS_SUMMARY =
  '你不再只是「想写好纪要」，而是有了一份能直接用的总结方法'

export const NEXT_WEEK_SUGGESTION = {
  quest_title: '进入「文档写作副本」',
  description: '把会议总结能力延伸到日常文档输出，练一份结构清晰的工作说明',
}

export const DOWNGRADE_OPTIONS = [
  {
    option_id: '5min',
    title: '5 分钟版',
    description: '回忆最近一场会，写下会议名 + 1 个你还记得的结论，两句话就够。',
    estimated_time: '5 分钟',
    event_title: '5 分钟版：写下一场会的名字 + 1 个结论',
    event_description:
      '回忆最近一场会，写下会议名称和你还记得的 1 个结论或待办。不用四格，两句话就够。',
    meaning: '今天先完成「开始记录」比完成「完美纪要」更重要。你已经迈出了最难的第一步。',
    output_type: 'checkbox' as const,
  },
  {
    option_id: 'step1',
    title: '只做第一步',
    description: '只填四格模板里的「决议」一格，其他先空着。',
    estimated_time: '5 分钟',
    event_title: '只做第一步：填「决议」一格',
    event_description: '只填四格模板里的「决议」一格，其他先空着。',
    meaning: '今天先完成一小步，比完全不做更有价值。',
    output_type: 'checkbox' as const,
  },
  {
    option_id: 'tomorrow',
    title: '明天继续',
    description: '今天先休息，明天从原任务继续，不判失败。',
    estimated_time: '0 分钟',
    event_title: '',
    event_description: '',
    meaning: '',
    output_type: 'checkbox' as const,
  },
]
