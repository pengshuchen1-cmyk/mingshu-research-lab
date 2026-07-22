"""Add event types discovered from real master-case samples.

This script keeps master-case observations from becoming dangling labels.
Each new event is added with the same evidence-chain fields required by the
monthly event quality gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"

CORE_SOURCES = [
    "yuan_hai_zi_ping",
    "san_ming_tong_hui",
    "ming_li_tan_yuan",
    "yu_zhao_ding_zhen_jing",
    "wu_xing_jing_ji",
    "master_case_chen_pengshu_2026",
]

FORBIDDEN = [
    "必定",
    "绝对",
    "注定",
    "一定发财",
    "一定离婚",
    "必定破财",
    "必有灾",
    "必有大病",
    "短命",
    "一定买房",
    "必有车祸",
]

COMMON_CONFIDENCE = {
    "high": "至少命中4条证据，并且包含十神、喜用、宫位/大运流年中的至少3类依据。",
    "medium": "至少命中3条证据，但宫位或大运依据不足。",
    "low": "仅命中2条证据，只能作为轻度提醒，不进入优先Top事件。",
    "downgrade_reasons": [
        "忌神参与较重",
        "冲克过强",
        "证据只来自单一维度",
        "缺少宫位或现实场景支撑",
        "触发规则过于泛化",
        "反向条件被命中",
    ],
}

COMMON_PALACE = {
    "year_branch": "年支偏向长辈、家庭背景、外部圈层和旧有关系。",
    "month_branch": "月支偏向事业平台、上级同事、客户组织和主业环境。",
    "day_branch": "日支偏向伴侣、合作方、一对一关系和居住状态。",
    "hour_branch": "时支偏向项目结果、副业、晚辈、长期规划和收尾事项。",
}


def _load(name: str) -> Any:
    with (RULES_DIR / name).open(encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: Any) -> None:
    with (RULES_DIR / name).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _condition(ctype: str, *, value: Any = None, weight: float = 1.0, evidence_text: str) -> dict[str, Any]:
    item: dict[str, Any] = {
        "type": ctype,
        "weight": weight,
        "evidence_text": evidence_text,
        "source_ids": CORE_SOURCES,
    }
    if value is not None:
        item["value"] = value
    return item


def build_cooperation_opportunity() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    event_type = "cooperation_opportunity"
    rule_id = "rule_master_case_cooperation_opportunity"
    variants = [
        {
            "variant_id": "cooperation_opportunity_recruitment",
            "trigger_pattern": ["招募", "贵人", "资源", "喜用"],
            "one_line": "容易出现别人邀约、招募、牵线或介绍合作入口。",
            "real_world_signals": [
                "有人提出合作或邀请加入项目",
                "朋友、客户或上级介绍新机会",
                "出现可以先了解的小项目或资源入口",
            ],
            "risk_points": [
                "机会还在入口阶段，不等于已经落地",
                "要确认角色、分工、时间和收益边界",
            ],
            "advice": "先把对方是谁、要你做什么、你承担什么责任、是否有书面说明问清楚，再决定投入多少精力。",
        },
        {
            "variant_id": "cooperation_opportunity_cautious",
            "trigger_pattern": ["忌神", "冲", "压力", "责任"],
            "one_line": "合作机会伴随责任或压力时，更适合稳而行。",
            "real_world_signals": [
                "有人招募但条件还没有说透",
                "机会看起来不错，但需要你先承担责任",
                "亲友、熟人或同事牵线，容易夹杂人情压力",
            ],
            "risk_points": [
                "口头承诺多，落地条款少",
                "责任扩大但收益不清",
                "因为熟人关系不好拒绝",
            ],
            "advice": "把机会拆成试做、观察、确认三步，不急着签长期承诺，先看现实成本和对方执行力。",
        },
    ]
    ontology = {
        "event_type": event_type,
        "label": "合作机会",
        "category": "事业项目",
        "description": "有人招募、牵线、介绍资源或提出合作入口时，可作为合作机会观察，不等同于正式合作已经落地。",
        "possible_real_world_forms": [
            "有人招募合作",
            "新项目邀约",
            "资源牵线",
            "熟人介绍机会",
        ],
        "trigger_rules": [rule_id],
        "evidence_template": "触发因素：{evidence}。现实观察：{forms}。",
        "variants": [item["variant_id"] for item in variants],
        "risk_points": [
            "机会入口和正式合作要分开看",
            "角色分工不清",
            "熟人牵线伴随人情压力",
        ],
        "safe_expression": "本月较容易出现合作机会或招募信号，建议先了解条件，再稳步推进。",
        "forbidden_expression": FORBIDDEN,
        "default_probability_level": "需观察",
        "source_ids": CORE_SOURCES,
        "basis": "合作机会来自真实师傅样本的“有人招募合作、有新机遇、要求稳而行”，结合印星贵人、食伤表达、财星客户、官杀责任与月支事业平台共同判断。",
        "traditional_basis": {
            "ten_god_basis": [
                "印星主长辈、老师、顾问、平台保护和专业人士牵线。",
                "食伤主表达、传播、展示和把能力说出去。",
                "财星主客户、资源、订单和交易对象。",
                "官杀主责任、职位、规则和上级招募。",
                "比劫主同辈、同行、朋友和团队邀约。",
            ],
            "element_basis": [
                "木象偏成长、招募、计划和新机会。",
                "水象偏信息流动、介绍、跨圈层连接。",
                "火象偏曝光、表达和被看见。",
            ],
            "branch_relation_basis": [
                "月支代表事业平台和主业环境，被引动时更容易出现工作合作入口。",
                "日支代表合作方和一对一关系，被引动时更需要确认角色边界。",
                "年支代表亲友、长辈和旧关系，触发时可能由熟人或亲人牵线。",
            ],
            "shensha_basis": [
                "天乙贵人、人缘象和驿马象只作为辅助加权，不单独决定合作机会。",
                "真实师傅样本中的招募合作用于补充现实应事，不直接替代主结构判断。",
            ],
            "source_ids": CORE_SOURCES,
        },
        "structure_basis": {
            "required_patterns": [
                "印星、食伤、财星、官杀、比劫或月支事业环境至少两项共同出现。",
                "必须落到招募、邀约、牵线、介绍、试合作或新项目入口等现实场景。",
            ],
            "supporting_patterns": [
                "有贵人或熟人介绍",
                "有项目入口但尚未形成正式合同",
                "有责任增加或角色变化提示",
                "师傅样本显示新机遇需要稳而行",
            ],
            "risk_patterns": [
                "机会说得多但条款少",
                "责任先增加但收益不清",
                "人情关系导致不好拒绝",
                "忌神或冲动较重时需要降级观察",
            ],
        },
        "palace_basis": {
            **COMMON_PALACE,
            "specific_focus": [
                "事业平台",
                "合作方",
                "熟人牵线",
                "亲人或旧关系带来的机会入口",
            ],
        },
        "modern_mapping": {
            "positive_expression": [
                "有人招募合作",
                "出现新项目入口",
                "有人牵线介绍资源",
            ],
            "neutral_expression": [
                "机会需要先了解条件",
                "合作可能还停留在口头邀约阶段",
                "要确认角色、分工和收益边界",
            ],
            "negative_expression": [
                "机会伴随责任增加",
                "熟人关系带来人情压力",
                "条件不清时容易后续反复",
            ],
        },
        "confidence_basis": COMMON_CONFIDENCE,
        "anti_triggers": [
            "忌神参与较重",
            "冲克过强",
            "只有口头邀约没有现实事项",
            "责任和收益明显不对等",
            "合作方背景不清",
        ],
        "user_visible_basis": "合作机会看的是谁来找你、为什么找你、要你承担什么，以及这个机会有没有真实项目、资源或客户支撑。",
        "required_evidence_count": 2,
        "subtype_rules": {
            "上级招募型": ["官杀或月支事业平台引动", "职位责任增加", "需要确认职责"],
            "朋友牵线型": ["比劫或年支旧关系引动", "熟人介绍机会", "需要守住人情边界"],
            "客户资源型": ["财星或客户入口引动", "资源方提出合作", "要确认款项和交付"],
            "专业人士推荐型": ["印星引动", "老师顾问或平台推荐", "适合先做资料核验"],
            "表达曝光型": ["食伤引动", "作品或表达带来邀约", "注意别承诺过多"],
        },
    }
    rule = {
        "rule_id": rule_id,
        "target_event_type": event_type,
        "min_trigger_count": 3,
        "trigger_conditions": [
            _condition("is_resource_month", evidence_text="印星月更容易出现老师、顾问、平台或专业人士带来的机会入口。"),
            _condition("is_output_month", evidence_text="食伤月容易通过表达、展示、作品或沟通被别人看见。"),
            _condition("is_wealth_month", evidence_text="财星月更容易接触客户、资源方和交易对象。"),
            _condition("is_officer_month", evidence_text="官杀月容易出现上级、职位、责任或规则牵引的招募。"),
            _condition("clash_month_branch", weight=1.1, evidence_text="月支代表事业平台，被冲动时主业环境更容易出现新入口。"),
            _condition("clash_day_branch", weight=1.0, evidence_text="日支代表合作方，被冲动时一对一合作关系更需要确认边界。"),
            _condition(
                "group_count_at_least",
                value=[{"group": "resource", "min": 1}, {"group": "output", "min": 1}, {"group": "wealth", "min": 1}],
                weight=0.8,
                evidence_text="原局有印、食伤或财星支撑时，机会更容易落到介绍、表达或资源交易。",
            ),
            _condition("favorable_relation", value=["喜用相关", "平稳观察"], weight=0.7, evidence_text="喜用或平稳月份更适合先了解机会和试推进。"),
        ],
        "source_ids": CORE_SOURCES,
        "basis": "合作机会不靠单一贵人或合作字眼触发，需同时观察印星牵线、食伤表达、财星资源、官杀责任、月支事业平台或合作方宫位。",
        "confidence": "master-case evidence-chain event",
    }
    return ontology, rule, variants


def main() -> None:
    ontology = _load("monthly_event_ontology.json")
    trigger_rules = _load("monthly_event_trigger_rules.json")
    variants = _load("monthly_event_variants.json")

    event, rule, event_variants = build_cooperation_opportunity()
    event_type = event["event_type"]

    ontology[event_type] = event

    trigger_rules = [
        item for item in trigger_rules
        if item.get("target_event_type") != event_type and item.get("rule_id") != rule["rule_id"]
    ]
    trigger_rules.append(rule)

    variants[event_type] = event_variants

    _save("monthly_event_ontology.json", ontology)
    _save("monthly_event_trigger_rules.json", trigger_rules)
    _save("monthly_event_variants.json", variants)

    print(f"added or updated master-case event type: {event_type}")


if __name__ == "__main__":
    main()
