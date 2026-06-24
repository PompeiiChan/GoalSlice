"""完成反馈静态模板（LLM fallback / Demo 对齐 mocks/data DAY_FEEDBACK）。"""

from typing import TypedDict


class FeedbackTemplate(TypedDict):
    action_label: str
    meaning_text: str
    asset_name: str
    asset_type: str


FEEDBACK_BY_DAY: dict[int, FeedbackTemplate] = {
    1: {
        "action_label": "会议场景梳理",
        "meaning_text": (
            "你不再只是「想写好纪要」，而是先锁定了最难总结的场景。知道难点在哪，练习才有方向。"
        ),
        "asset_name": "总结场景卡",
        "asset_type": "ability_fragment",
    },
    2: {
        "action_label": "缺失信息识别",
        "meaning_text": "你开始用「缺什么」的视角审视纪要，这比盲目重写更有针对性。",
        "asset_name": "总结场景卡",
        "asset_type": "ability_fragment",
    },
    3: {
        "action_label": "四格模板练习",
        "meaning_text": (
            "你第一次把「我想提升会议总结能力」从模糊感受，变成了可重复使用的结构。"
            "以后每场会都有抓手，而不是听完就散。"
        ),
        "asset_name": "总结模板碎片",
        "asset_type": "template_fragment",
    },
    4: {
        "action_label": "范例拆解",
        "meaning_text": "你从优秀范例中提炼了可学习的写法，这比从零摸索更快建立标准。",
        "asset_name": "总结范例",
        "asset_type": "case_note",
    },
    5: {
        "action_label": "核心结论提炼",
        "meaning_text": "你用 5 句话概括了一场会的要点，精炼表达是完整纪要的必经之路。",
        "asset_name": "总结模板碎片",
        "asset_type": "template_fragment",
    },
    6: {
        "action_label": "专属模板整理",
        "meaning_text": "你把本周练习过的结构整理成了可复用模板，以后每场会都有固定抓手。",
        "asset_name": "总结模板碎片",
        "asset_type": "template_fragment",
    },
    7: {
        "action_label": "Boss 战总结稿",
        "meaning_text": (
            "你完成了本周 Boss 战——一份真实会议的完整总结稿。"
            "你不再只是「想写好纪要」，而是有了一份能直接用的总结方法。"
        ),
        "asset_name": "总结范例",
        "asset_type": "case_note",
    },
}


def get_feedback_template(day_index: int) -> FeedbackTemplate:
    return FEEDBACK_BY_DAY.get(day_index, FEEDBACK_BY_DAY[3])
