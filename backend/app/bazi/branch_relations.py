"""地支关系基础判断。"""

from __future__ import annotations

BRANCH_CLASH_PAIRS = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}

PILLAR_LABELS = {
    "year": "年支",
    "month": "月支",
    "day": "日支",
    "hour": "时支",
}

PILLAR_CLASH_TEXT = {
    "year": "容易涉及家庭背景、长辈、外部环境、人际圈层变化。",
    "month": "容易涉及事业环境、工作节奏、上级同事、主业方向变化。",
    "day": "容易涉及感情关系、伴侣关系、合作关系、居住状态变化。",
    "hour": "容易涉及子女、长期规划、副业成果、晚间状态、项目收尾变化。",
}


def get_branch_clash(branch_a: str, branch_b: str) -> bool:
    """
    判断两个地支是否形成六冲。
    """
    if not branch_a or not branch_b:
        return False
    return frozenset((branch_a, branch_b)) in BRANCH_CLASH_PAIRS


def analyze_year_branch_relations(chart: dict, year_zhi: str) -> list[dict]:
    """
    判断流年地支与原局四支的基础六冲关系。
    """
    relations: list[dict] = []
    pillars = chart.get("pillars", {})
    for pillar_key in ["year", "month", "day", "hour"]:
        native_zhi = pillars.get(pillar_key, {}).get("zhi", "")
        if get_branch_clash(year_zhi, native_zhi):
            label = f"冲{PILLAR_LABELS[pillar_key]}"
            relations.append(
                {
                    "type": "六冲",
                    "label": label,
                    "target": PILLAR_LABELS[pillar_key],
                    "native_zhi": native_zhi,
                    "year_zhi": year_zhi,
                    "text": PILLAR_CLASH_TEXT[pillar_key],
                }
            )
    return relations
