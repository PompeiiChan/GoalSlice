"""降级方案静态模板 — 对齐 frontend/mocks/data.ts DOWNGRADE_OPTIONS。"""

from typing import TypedDict


class DowngradeOptionDisplay(TypedDict):
    option_id: str
    title: str
    description: str
    estimated_time: str


class DowngradeEventTemplate(TypedDict):
    option_id: str
    title: str
    description: str
    estimated_time: str
    event_title: str
    event_description: str
    meaning: str
    output_type: str


DOWNGRADE_TEMPLATES: list[DowngradeEventTemplate] = [
    {
        "option_id": "5min",
        "title": "5 分钟版",
        "description": "回忆最近一场会，写下会议名 + 1 个你还记得的结论，两句话就够。",
        "estimated_time": "5 分钟",
        "event_title": "5 分钟版：写下一场会的名字 + 1 个结论",
        "event_description": (
            "回忆最近一场会，写下会议名称和你还记得的 1 个结论或待办。"
            "不用四格，两句话就够。"
        ),
        "meaning": "今天先完成「开始记录」比完成「完美纪要」更重要。你已经迈出了最难的第一步。",
        "output_type": "checkbox",
    },
    {
        "option_id": "step1",
        "title": "只做第一步",
        "description": "只填四格模板里的「决议」一格，其他先空着。",
        "estimated_time": "5 分钟",
        "event_title": "只做第一步：填「决议」一格",
        "event_description": "只填四格模板里的「决议」一格，其他先空着。",
        "meaning": "今天先完成一小步，比完全不做更有价值。",
        "output_type": "checkbox",
    },
    {
        "option_id": "tomorrow",
        "title": "明天继续",
        "description": "今天先休息，明天从原任务继续，不判失败。",
        "estimated_time": "0 分钟",
        "event_title": "",
        "event_description": "",
        "meaning": "",
        "output_type": "checkbox",
    },
]


def get_static_downgrade_options() -> list[DowngradeOptionDisplay]:
    return [
        {
            "option_id": t["option_id"],
            "title": t["title"],
            "description": t["description"],
            "estimated_time": t["estimated_time"],
        }
        for t in DOWNGRADE_TEMPLATES
    ]


def get_downgrade_template(option_id: str) -> DowngradeEventTemplate | None:
    for template in DOWNGRADE_TEMPLATES:
        if template["option_id"] == option_id:
            return template
    return None
