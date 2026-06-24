"""7 天计划静态模板（LLM 测试 Mock / 会议总结 Demo 对齐原型）。"""

from src.models.quest import QuestPreviewDayDTO, QuestPreviewDTO

MVP_GOAL_TYPES = frozenset(
    {
        "career_switch",
        "skill_up",
        "interview_prep",
        "portfolio",
        "personal_brand",
        "expression",
        "promotion",
    }
)

OUT_OF_SCOPE_MESSAGE = "该目标暂不在 MVP 支持范围内，建议聚焦职业成长与技能提升"

DAILY_EVENT_TITLE_OVERRIDE: dict[int, str] = {
    3: "用四格模板填空总结一场会",
}

_WEEK_PLAN_DAYS: list[QuestPreviewDayDTO] = [
    QuestPreviewDayDTO(
        day_index=1,
        event_title="列出最近 3 场会，标出最难总结的一场",
        event_description="回忆本周参加过的会议，写下名称并标出最难总结的一场。",
        estimated_time="15 分钟",
        meaning="先定位难点，后续练习才有的放矢。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=2,
        event_title="读一份旧纪要，圈出缺失的 3 个关键信息",
        event_description="找一份你写过的或收到的会议纪要，圈出缺失的背景、决议或待办。",
        estimated_time="15 分钟",
        meaning="知道「缺什么」比盲目重写更有针对性。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=3,
        event_title="用「背景-讨论-决议-待办」四格模板，填空总结一场会",
        event_description=(
            "选一场你最近参加的会，按「背景 → 讨论 → 决议 → 待办」四格，每格写 1–2 句话。"
        ),
        estimated_time="15 分钟",
        meaning="四格模板把模糊感受变成固定结构，你先求「写完」，再求「写好」。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=4,
        event_title="找一份好纪要范例，标出 2 个可学习的写法",
        event_description="找一份你觉得写得好的会议纪要，标出 2 个值得学习的写法或结构。",
        estimated_time="20 分钟",
        meaning="从范例中学习比从零摸索更快建立标准。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=5,
        event_title="用 5 句话写出一场会的核心结论",
        event_description="选一场会，用 5 句话概括背景、讨论要点、决议和待办。",
        estimated_time="15 分钟",
        meaning="精炼表达是完整纪要的必经之路。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=6,
        event_title="整理成你的专属会议总结模板",
        event_description="把本周练习过的结构整理成一份可复用的会议总结模板。",
        estimated_time="25 分钟",
        meaning="模板化让每次会议都有固定抓手。",
        output_type="text",
        is_boss=False,
    ),
    QuestPreviewDayDTO(
        day_index=7,
        event_title="Boss 战：独立完成一场真实会议的总结稿",
        event_description="选一场真实会议，产出完整总结稿（含背景、决议、待办）。",
        estimated_time="30 分钟",
        meaning="本周成果沉淀。",
        output_type="text",
        is_boss=True,
    ),
]


def build_meeting_summary_preview() -> QuestPreviewDTO:
    return QuestPreviewDTO(
        quest_title="从「会议听完就忘」到「能写出可执行的会议总结」",
        success_condition="完成一份真实会议的总结稿（含背景、决议、待办）",
        total_estimated_time="每天约 15–30 分钟，共 7 天",
        days=list(_WEEK_PLAN_DAYS),
    )


def build_quest_generate_prompt(
    raw_goal: str,
    refined_goal: str,
    weekly_outcome: str,
    available_time: str,
    current_level: str,
    failure_reason: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是职业成长教练，为用户生成 7 天可执行的小步计划。"
                "必须输出 JSON，包含 quest_title、success_condition、total_estimated_time、"
                "days（长度恰好 7，day_index 1-7，第 7 天 is_boss=true）。"
                "每天字段：day_index, event_title, event_description, estimated_time, "
                "meaning, output_type（固定 text）, is_boss。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"目标：{raw_goal}\n精炼目标：{refined_goal}\n"
                f"本周期望：{weekly_outcome}\n每日可投入：{available_time}\n"
                f"当前水平：{current_level}\n常见卡点：{failure_reason}\n"
                "请生成 7 天职业成长主线预览。"
            ),
        },
    ]
