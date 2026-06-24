"""周复盘静态模板（LLM fallback / Demo 对齐 mocks/data）。"""

REVIEW_OUTPUTS = [
    "列出 3 场难总结的会议场景",
    "找出旧纪要里缺失的关键信息",
    "完成一次四格模板填空练习",
    "拆解一份优秀纪要范例",
    "写出一场会的 5 句核心结论",
]

REVIEW_OBSERVATION = "你在填空和拆解类任务上完成度高，写完整段落时容易拖延。"

REVIEW_BOSS_SUMMARY = "你不再只是「想写好纪要」，而是有了一份能直接用的总结方法"

NEXT_WEEK_SUGGESTION = {
    "quest_title": "进入「文档写作副本」",
    "description": "把会议总结能力延伸到日常文档输出，练一份结构清晰的工作说明",
}


def build_static_review(
    completed_count: int,
    outputs: list[str],
    assets: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "completed_count": completed_count,
        "total_days": 7,
        "outputs": outputs or REVIEW_OUTPUTS[: max(completed_count, 1)],
        "assets": assets,
        "observations": [REVIEW_OBSERVATION],
        "boss_summary": REVIEW_BOSS_SUMMARY,
        "next_week_suggestion": dict(NEXT_WEEK_SUGGESTION),
    }
