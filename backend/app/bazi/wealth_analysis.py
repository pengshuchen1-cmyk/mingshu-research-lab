"""Rule-driven wealth analysis separated into earning and retention."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
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
class WealthAnalysis:
    earning_channels: tuple[Evidence, ...]
    retention_factors: tuple[Evidence, ...]
    risk_factors: tuple[Evidence, ...]
    public_text: str
    rule_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        all_evidence = self.earning_channels + self.retention_factors + self.risk_factors
        return {
            "earning_channels": [item.to_dict() for item in self.earning_channels],
            "retention_factors": [item.to_dict() for item in self.retention_factors],
            "risk_factors": [item.to_dict() for item in self.risk_factors],
            "evidence": [item.to_dict() for item in all_evidence],
            "public_text": self.public_text,
            "rule_ids": list(self.rule_ids),
        }


def analyze_wealth(chart: dict) -> WealthAnalysis:
    counts = chart.get("ten_god_counts", {})
    strength = str(chart.get("day_master_strength", {}).get("strength", "暂无法判断"))
    wealth_count = int(counts.get("正财", 0)) + int(counts.get("偏财", 0))
    output_count = int(counts.get("食神", 0)) + int(counts.get("伤官", 0))
    peer_count = int(counts.get("比肩", 0)) + int(counts.get("劫财", 0))
    visible_gods = {
        value.get("gan", "")
        for value in chart.get("ten_gods", {}).values()
        if isinstance(value, dict)
    }
    visible_wealth = sorted(visible_gods & {"正财", "偏财"})

    earning = [
        Evidence(
            "财星可见度",
            "WEALTH-STAR-VISIBILITY",
            "support" if wealth_count else "mixed",
            f"财星共{wealth_count}处，透干为{'、'.join(visible_wealth) or '未见'}",
            "财星显示对客户、资源、项目回报和现实收入的敏感度，但不等同现实资产数额。",
        ),
        Evidence(
            "生财路径",
            "WEALTH-REVENUE-RETENTION",
            "support" if output_count else "mixed",
            f"食伤共{output_count}处",
            "食伤较清楚时，更适合把技能、产品、内容或服务输出转为收入。",
        ),
    ]
    retention = [
        Evidence(
            "承财能力",
            "WEALTH-CAPACITY",
            "support" if strength in {"身强", "中和", "从旺"} else "mixed",
            f"日主强弱为{strength}",
            "承接项目规模要与自身资源、团队、时间和现金流能力匹配。",
        ),
        Evidence(
            "分账边界",
            "WEALTH-REVENUE-RETENTION",
            "pressure" if peer_count >= 3 else "mixed",
            f"比劫共{peer_count}处",
            "比劫越集中，越需要提前写清合伙投入、分账、回款和退出条件。",
        ),
    ]
    risk = [
        Evidence(
            "杠杆风险",
            "WEALTH-RISK-ADVICE",
            "pressure",
            "借贷、抵押和高杠杆会放大现金流波动",
            "命盘不能保证高杠杆项目结果；应先验证最坏情景、还款来源和退出机制。",
        )
    ]
    earning_text = "；".join(item.explanation for item in earning)
    retention_text = "；".join(item.explanation for item in retention)
    public_text = (
        f"赚钱路径：{earning_text}。留财条件：{retention_text}。"
        "风险提醒：抵押、借贷或扩大规模前，应以现实现金流和可承受损失为准。"
    )
    return WealthAnalysis(
        tuple(earning),
        tuple(retention),
        tuple(risk),
        public_text,
        (
            "WEALTH-STAR-VISIBILITY",
            "WEALTH-CAPACITY",
            "WEALTH-REVENUE-RETENTION",
            "WEALTH-RISK-ADVICE",
        ),
    )
