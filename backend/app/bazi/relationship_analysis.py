"""Rule-driven relationship stages and uncertainty handling."""

from __future__ import annotations

from dataclasses import dataclass

from .branch_relations import get_branch_clash

COMBINATION_PAIRS = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}
PEACH_BY_GROUP = {
    "申": "酉", "子": "酉", "辰": "酉",
    "寅": "卯", "午": "卯", "戌": "卯",
    "亥": "子", "卯": "子", "未": "子",
    "巳": "午", "酉": "午", "丑": "午",
}


@dataclass(frozen=True)
class RelationshipEvidence:
    dimension: str
    rule_id: str
    polarity: str
    fact: str
    explanation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "dimension": self.dimension,
            "rule_id": self.rule_id,
            "polarity": self.polarity,
            "fact": self.fact,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class RelationshipAnalysis:
    attraction_signals: tuple[RelationshipEvidence, ...]
    formation_signals: tuple[RelationshipEvidence, ...]
    stability_signals: tuple[RelationshipEvidence, ...]
    uncertainty: tuple[str, ...]
    current_status: str
    public_text: str
    rule_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        evidence = self.attraction_signals + self.formation_signals + self.stability_signals
        return {
            "attraction_signals": [item.to_dict() for item in self.attraction_signals],
            "formation_signals": [item.to_dict() for item in self.formation_signals],
            "stability_signals": [item.to_dict() for item in self.stability_signals],
            "evidence": [item.to_dict() for item in evidence],
            "uncertainty": list(self.uncertainty),
            "current_status": self.current_status,
            "public_text": self.public_text,
            "rule_ids": list(self.rule_ids),
        }


def analyze_relationship(chart: dict) -> RelationshipAnalysis:
    profile = chart.get("profile", {})
    female = str(profile.get("gender", "")).lower() in {"女", "female", "f"}
    counts = chart.get("ten_god_counts", {})
    spouse_names = ("正官", "七杀") if female else ("正财", "偏财")
    spouse_count = sum(int(counts.get(name, 0)) for name in spouse_names)
    pillars = chart.get("pillars", {})
    branches = {
        key: str(pillars.get(key, {}).get("zhi", ""))
        for key in ("year", "month", "day", "hour")
    }
    day_branch = branches["day"]
    peach = PEACH_BY_GROUP.get(day_branch, "")
    peach_positions = [key for key, branch in branches.items() if branch and branch == peach]
    clashes = [
        f"{day_branch}{branch}冲"
        for key, branch in branches.items()
        if key != "day" and get_branch_clash(day_branch, branch)
    ]
    combinations = [
        f"{day_branch}{branch}合"
        for key, branch in branches.items()
        if key != "day" and branch and frozenset((day_branch, branch)) in COMBINATION_PAIRS
    ]

    attraction = (
        RelationshipEvidence(
            "吸引与桃花",
            "REL-STAGES",
            "support" if peach_positions else "mixed",
            f"以日支{day_branch}取桃花{peach or '待定'}，命局见于{'、'.join(peach_positions) or '未集中'}",
            "桃花只代表被注意和互动机会，不等同关系已经建立。",
        ),
    )
    formation = (
        RelationshipEvidence(
            "对象出现与关系建立",
            "REL-SPOUSE-STAR",
            "support" if spouse_count else "mixed",
            f"{'官杀' if female else '财星'}共{spouse_count}处",
            "配偶星需要与夫妻宫及运年触发共同观察，不能只凭数量判断婚期。",
        ),
    )
    stability = (
        RelationshipEvidence(
            "夫妻宫稳定条件",
            "REL-PALACE-STABILITY",
            "pressure" if clashes else "support" if combinations else "mixed",
            f"日支{day_branch}；合为{'、'.join(combinations) or '无'}；冲为{'、'.join(clashes) or '无'}",
            "有合重在边界与承诺落实，有冲重在变化和沟通管理；两者都不直接等于婚姻结果。",
        ),
    )
    uncertainty = ("出生盘不能确认当前是否已婚，只能分析关系倾向、触发条件与时机。",)
    public_text = (
        f"吸引阶段：{attraction[0].explanation}关系建立：{formation[0].explanation}"
        f"稳定阶段：{stability[0].explanation}建议结合现实互动和大运流年分阶段验证。"
    )
    return RelationshipAnalysis(
        attraction,
        formation,
        stability,
        uncertainty,
        "unknown",
        public_text,
        ("REL-SPOUSE-STAR", "REL-PALACE-STABILITY", "REL-STAGES", "REL-STATUS-UNKNOWN"),
    )
