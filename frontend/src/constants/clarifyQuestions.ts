import type { ClarifyQuestion } from '@/types/goal'

/** 澄清题库 — 与原型 / mocks/data.ts / 后端 clarify_data.py 一致 */
export const CLARIFY_QUESTIONS: ClarifyQuestion[] = [
  {
    question_id: 'goal_type',
    question: '这个目标更接近哪一类？',
    options: ['转行 / 求职', '技能提升', '面试准备', '作品集建设', '个人品牌', '其他'],
  },
  {
    question_id: 'weekly_outcome',
    question: '如果只看这一周，你希望自己发生什么变化？',
    options: [
      '完成一个具体产物',
      '明确下一步方向',
      '开始行动，不再只想',
      '为面试 / 求职做一个准备动作',
      '解决一个卡点',
    ],
  },
  {
    question_id: 'available_time',
    question: '你每天大概能投入多久？',
    options: ['5 分钟', '15 分钟', '30 分钟', '60 分钟以上', '不固定，看当天状态'],
  },
  {
    question_id: 'current_level',
    question: '你现在更接近哪种状态？',
    options: [
      '完全小白，不知道从哪开始',
      '有一点了解，但不系统',
      '已经做过一些尝试',
      '有一定基础，但缺少成果',
      '已经比较明确，只是缺少执行节奏',
    ],
  },
  {
    question_id: 'failure_reason',
    question: '过去类似目标最容易卡在哪里？',
    options: [
      '不知道第一步做什么',
      '计划太复杂，坚持不下去',
      '太忙，没有固定时间',
      '学了一堆，但没有产出',
      '容易想太多，迟迟不开始',
    ],
  },
]
