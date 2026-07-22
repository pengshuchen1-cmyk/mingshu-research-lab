"""Audit a real master monthly case against current system Top 3 events.

This tool is intentionally read-heavy: it compares the recorded master case
with the same monthly event pipeline used by the Streamlit yearly page and
export page, then writes a Markdown calibration report.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASE_PATH = ROOT / "rules" / "master_case_references.json"
REPORT_DIR = ROOT / "docs" / "reports"
REPORT_PATH = REPORT_DIR / "master_case_chen_pengshu_2026_calibration_audit.md"


RELATED_EVENT_GROUPS: dict[str, set[str]] = {
    "social_drinking": {
        "social_drinking", "banquet_party", "favor_obligation", "friend_request",
        "networking", "old_friend_contact", "social_resource_cluster",
    },
    "vehicle_safety": {
        "vehicle_safety", "safety_attention", "travel_traffic", "vehicle_expense",
        "vehicle_repair", "traffic_ticket", "route_change", "expense_vehicle_cluster",
    },
    "safety_attention": {
        "safety_attention", "vehicle_safety", "travel_traffic", "travel_delay",
        "route_change", "traffic_ticket", "expense_vehicle_cluster", "sudden_change_warning",
    },
    "impulsive_decision": {
        "impulsive_decision", "minor_loss", "hidden_cost", "rule_penalty",
        "misunderstanding_risk", "official_dispute",
    },
    "project_progress": {
        "project_progress", "project_breakthrough", "business_negotiation",
        "cooperation_opportunity", "business_partnership", "contract_cooperation_cluster",
    },
    "business_negotiation": {
        "business_negotiation", "business_partnership", "cooperation_opportunity",
        "contract_cooperation_cluster", "cooperation_boundary",
    },
    "responsibility_increase": {
        "responsibility_increase", "boss_pressure", "performance_review",
        "overwork", "contract_cooperation_cluster",
    },
    "business_partnership": {
        "business_partnership", "cooperation_opportunity", "business_negotiation",
        "contract_cooperation_cluster", "cooperation_boundary",
    },
    "cooperation_opportunity": {
        "cooperation_opportunity", "business_partnership", "business_negotiation",
        "referral_opportunity", "resource_connection", "contract_cooperation_cluster",
    },
    "project_breakthrough": {
        "project_breakthrough", "project_progress", "business_surprise",
        "cooperation_opportunity", "salary_bonus",
    },
    "nobleman_help": {
        "nobleman_help", "mentor_advice", "hidden_help", "platform_support",
        "resource_connection", "referral_opportunity", "family_support",
    },
    "family_issue": {
        "family_issue", "family_pressure", "family_support", "elder_issue",
        "parent_health_attention", "family_responsibility", "relationship_family_cluster", "child_family_responsibility",
    },
    "favor_obligation": {
        "favor_obligation", "friend_request", "human_cost", "social_spending",
        "social_resource_cluster", "gift_expense",
    },
    "debt_borrowing": {
        "debt_borrowing", "debt_loss", "cashflow_pressure", "cooperation_money",
        "expense_cashflow_cluster", "expense_pressure_cluster",
    },
    "cashflow_pressure": {
        "cashflow_pressure", "debt_borrowing", "debt_loss", "wealth_outflow",
        "expense_cashflow_cluster", "expense_pressure_cluster",
    },
    "investment_risk": {
        "investment_risk", "debt_loss", "cashflow_pressure", "minor_loss",
        "hidden_cost", "expense_cashflow_cluster",
    },
    "wealth_outflow": {
        "wealth_outflow", "cashflow_pressure", "debt_loss", "human_cost",
        "expense_pressure_cluster", "expense_social_cluster", "expense_cashflow_cluster",
    },
    "business_surprise": {
        "business_surprise", "project_breakthrough", "unexpected_income",
        "wealth_inflow", "client_payment", "business_cash_in",
    },

    "travel_traffic": {
        "travel_traffic", "safety_attention", "vehicle_safety",
        "travel_delay", "route_change", "sudden_change_warning",
    },
    "travel_delay": {
        "travel_delay", "travel_traffic", "route_change", "long_distance_travel",
        "vehicle_safety", "expense_vehicle_cluster",
    },

    "fire_anxiety": {
        "fire_anxiety", "emotional_pressure", "health_fluctuation",
        "overwork", "recovery_rest",
    },
    "health_fluctuation": {
        "health_fluctuation", "overwork", "recovery_rest", "emotional_pressure",
        "medical_attention", "illness_symbol_attention",
    },
    "overwork": {
        "overwork", "health_fluctuation", "emotional_pressure", "recovery_rest",
        "shoulder_neck_issue",
    },
    "minor_loss": {
        "minor_loss", "wealth_outflow", "hidden_cost", "equipment_fault",
        "expense_pressure_cluster",
    },
    "gossip_dispute": {
        "gossip_dispute", "misunderstanding_risk", "official_dispute",
        "dispute_mediation", "relationship_pressure_cluster",
    },
    "misunderstanding_risk": {
        "misunderstanding_risk", "misunderstanding", "gossip_dispute",
        "relationship_communication_cluster", "dispute_mediation",
    },
    "relationship_progress": {
        "relationship_progress", "partner_planning", "confession_signal",
        "marriage_discussion", "peach_blossom_contact", "relationship_family_cluster", "partner_tolerance",
    },
    "partner_planning": {
        "partner_planning", "relationship_progress", "marriage_discussion",
        "relationship_family_cluster", "partner_tolerance",
    },
    "store_operation": {
        "store_operation", "shop_property", "business_cash_in", "operation_cost",
        "business_partnership",
    },
    "property_housing": {
        "property_housing", "asset_purchase", "shop_property", "home_repair",
        "rental_move", "living_environment_change", "expense_repair_cluster",
    },
    "shop_property": {
        "shop_property", "store_operation", "property_housing", "asset_purchase",
        "rental_move",
    },
    "asset_purchase": {
        "asset_purchase", "property_housing", "shop_property", "equipment_purchase",
        "vehicle_expense", "expense_vehicle_cluster", "expense_repair_cluster",
    },
    "vehicle_expense": {
        "vehicle_expense", "vehicle_repair", "vehicle_safety", "travel_traffic",
        "asset_purchase", "expense_vehicle_cluster",
    },
    "emotional_pressure": {
        "emotional_pressure", "overwork", "health_fluctuation", "recovery_rest",
        "relationship_pressure_cluster",
    },
    "official_dispute": {
        "official_dispute", "legal_compliance", "rule_penalty", "dispute_mediation",
        "contract_boundary_cluster", "contract_compliance_cluster", "sudden_change_warning",
    },
    "rule_penalty": {
        "rule_penalty", "official_dispute", "legal_compliance", "traffic_ticket",
        "penalty_fee", "contract_compliance_cluster",
    },
    "legal_compliance": {
        "legal_compliance", "official_dispute", "rule_penalty",
        "contract_compliance_cluster", "contract_boundary_cluster", "sudden_change_warning",
    },
    "equipment_purchase": {
        "equipment_purchase", "asset_purchase", "repair_expense",
        "expense_repair_cluster", "expense_pressure_cluster",
    },
    "sudden_change_warning": {
        "sudden_change_warning", "travel_delay", "impulsive_decision",
        "official_dispute", "rule_penalty", "legal_compliance",
    },
    "trapped_commitment": {
        "trapped_commitment", "cashflow_pressure", "investment_risk",
        "delayed_issue", "relationship_conflict", "cooperation_boundary",
        "emotional_pressure",
    },
    "short_term_cooperation": {
        "short_term_cooperation", "business_partnership", "cooperation_opportunity",
        "cooperation_boundary", "contract_document", "approval_process",
    },
    "female_friend_social": {
        "female_friend_social", "friend_request", "networking",
        "social_boundary", "family_issue", "old_friend_contact",
    },
    "business_procedure_handling": {
        "business_procedure_handling", "approval_process", "contract_document",
        "business_negotiation", "document_error", "license_document",
    },
    "child_family_responsibility": {
        "child_family_responsibility", "family_responsibility", "family_issue",
        "parent_health_attention", "family_discussion",
    },
    "partner_tolerance": {
        "partner_tolerance", "partner_planning", "relationship_progress",
        "relationship_conflict", "emotional_pressure",
    },
}


MASTER_CASE_CHAIN_RELATED_UPDATES = {
    "travel_traffic": {"travel_traffic", "safety_attention", "vehicle_safety", "travel_delay", "route_change", "sudden_change_warning"},
    "travel_delay": {"travel_delay", "travel_traffic", "safety_attention", "vehicle_safety", "route_change", "sudden_change_warning"},
    "official_dispute": {"official_dispute", "legal_compliance", "rule_penalty", "dispute_mediation", "contract_boundary_cluster", "contract_compliance_cluster", "sudden_change_warning"},
    "rule_penalty": {"rule_penalty", "official_dispute", "legal_compliance", "traffic_ticket", "penalty_fee", "contract_compliance_cluster", "sudden_change_warning"},
    "legal_compliance": {"legal_compliance", "official_dispute", "rule_penalty", "contract_compliance_cluster", "contract_boundary_cluster", "sudden_change_warning"},
    "emotional_pressure": {"emotional_pressure", "overwork", "health_fluctuation", "recovery_rest", "relationship_pressure_cluster", "fire_anxiety", "trapped_commitment", "partner_tolerance"},
    "fire_anxiety": {"fire_anxiety", "emotional_pressure", "health_fluctuation", "overwork", "recovery_rest"},
    "family_asset": {"family_asset", "asset_purchase", "property_housing", "shop_property", "vehicle_expense", "expense_vehicle_cluster"},
    "cashflow_pressure": {"cashflow_pressure", "debt_borrowing", "debt_loss", "wealth_outflow", "investment_risk", "trapped_commitment", "expense_cashflow_cluster", "expense_pressure_cluster", "expense_vehicle_cluster"},
    "investment_risk": {"investment_risk", "debt_loss", "cashflow_pressure", "minor_loss", "hidden_cost", "trapped_commitment", "expense_cashflow_cluster"},
    "asset_purchase": {"asset_purchase", "property_housing", "shop_property", "family_asset", "equipment_purchase", "vehicle_expense", "expense_vehicle_cluster", "expense_repair_cluster"},
    "property_housing": {"property_housing", "asset_purchase", "family_asset", "shop_property", "home_repair", "rental_move", "living_environment_change", "expense_repair_cluster", "expense_vehicle_cluster"},
    "vehicle_expense": {"vehicle_expense", "vehicle_repair", "vehicle_safety", "travel_traffic", "asset_purchase", "family_asset", "expense_vehicle_cluster"},
    "relationship_conflict": {"relationship_conflict", "misunderstanding", "relationship_pressure_cluster", "partner_tolerance", "trapped_commitment", "emotional_pressure"},
    "misunderstanding": {"misunderstanding", "relationship_conflict", "misunderstanding_risk", "relationship_communication_cluster", "partner_tolerance"},
    "delayed_issue": {"delayed_issue", "trapped_commitment", "work_block", "short_term_cooperation", "cashflow_pressure"},
    "friend_request": {"friend_request", "female_friend_social", "networking", "social_boundary", "social_drinking", "favor_obligation", "social_resource_cluster"},
    "social_boundary": {"social_boundary", "female_friend_social", "friend_request", "networking", "social_drinking", "favor_obligation", "social_resource_cluster"},
    "networking": {"networking", "female_friend_social", "friend_request", "social_boundary", "social_drinking", "resource_connection", "social_resource_cluster"},
    "social_drinking": {"social_drinking", "female_friend_social", "banquet_party", "favor_obligation", "friend_request", "networking", "old_friend_contact", "social_resource_cluster"},
    "business_negotiation": {"business_negotiation", "business_partnership", "cooperation_opportunity", "contract_cooperation_cluster", "cooperation_boundary", "business_procedure_handling", "approval_process"},
    "approval_process": {"approval_process", "business_procedure_handling", "contract_document", "contract_document_cluster", "contract_compliance_cluster", "business_negotiation"},
    "medical_attention": {"medical_attention", "health_fluctuation", "overwork", "recovery_rest", "fire_anxiety", "expense_health_cluster"},
    "health_fluctuation": {"health_fluctuation", "overwork", "recovery_rest", "emotional_pressure", "medical_attention", "illness_symbol_attention", "fire_anxiety"},
    "family_issue": {"family_issue", "family_pressure", "family_support", "elder_issue", "parent_health_attention", "family_responsibility", "child_family_responsibility", "relationship_family_cluster"},
    "family_responsibility": {"family_responsibility", "family_issue", "child_family_responsibility", "parent_health_attention", "family_discussion", "overwork"},
    "work_block": {"work_block", "delayed_issue", "overwork", "emotional_pressure", "trapped_commitment"},
    "partner_planning": {"partner_planning", "relationship_progress", "marriage_discussion", "relationship_family_cluster", "partner_tolerance"},
    "relationship_progress": {"relationship_progress", "partner_planning", "confession_signal", "marriage_discussion", "peach_blossom_contact", "relationship_family_cluster", "partner_tolerance"},
}
for _event_type, _related in MASTER_CASE_CHAIN_RELATED_UPDATES.items():
    RELATED_EVENT_GROUPS[_event_type] = set(RELATED_EVENT_GROUPS.get(_event_type, {_event_type})) | set(_related)


EVENT_LABEL_FALLBACKS = {
    "social_drinking": "饭局酒友",
    "vehicle_safety": "车辆驾驶提醒",
    "safety_attention": "出行安全提醒",
    "impulsive_decision": "改革三思/冲动决策",
    "project_progress": "项目推进",
    "business_negotiation": "商务谈判",
    "responsibility_increase": "责任增加",
    "business_partnership": "商业合作",
    "cooperation_opportunity": "合作机会",
    "project_breakthrough": "项目突破",
    "nobleman_help": "贵人协助",
    "family_issue": "家庭亲人事务",
    "favor_obligation": "人情请托",
    "debt_borrowing": "借贷担保",
    "cashflow_pressure": "现金流压力",
    "investment_risk": "投资谨慎",
    "wealth_outflow": "临时破财/支出",
    "business_surprise": "项目财务转机",
    "travel_delay": "行程延误/外部扰动",
    "health_fluctuation": "身体状态波动",
    "overwork": "耗气过劳",
    "minor_loss": "小额损耗",
    "gossip_dispute": "口舌小人",
    "misunderstanding_risk": "误会风险",
    "relationship_progress": "感情推进",
    "partner_planning": "伴侣规划",
    "store_operation": "门店经营",
    "property_housing": "房屋居住",
    "shop_property": "店铺门面",
    "asset_purchase": "大件添置",
    "vehicle_expense": "车辆支出",
    "emotional_pressure": "压力压抑",
    "official_dispute": "规则纠纷/报警边界",
    "rule_penalty": "规则处罚",
    "legal_compliance": "合规流程",
    "equipment_purchase": "设备采购",
    "family_issue": "家庭事务",
    "family_responsibility": "家庭责任",
    "travel_traffic": "通勤出行",
    "investment_risk": "投资谨慎",
    "work_block": "工作卡点",
    "delayed_issue": "拖延滞后",
    "relationship_conflict": "关系摩擦",
    "misunderstanding": "误会解释",
    "sales_conversion": "客户成交",
    "content_traffic": "内容流量",
    "resource_connection": "资源连接",
    "referral_opportunity": "转介绍机会",
    "old_friend_contact": "旧友联系",
    "customer_growth": "客户增长",
    "friend_request": "朋友求助",
    "social_boundary": "社交边界",
    "networking": "资源局",
    "unexpected_income": "临时收入",
    "business_cash_in": "经营现金流进入",
    "business_partnership": "商业合作",
    "sudden_change_warning": "忽然变化",
    "trapped_commitment": "被套住",
    "short_term_cooperation": "短合",
    "female_friend_social": "闺蜜亲友",
    "business_procedure_handling": "办业务",
    "child_family_responsibility": "子女事",
    "partner_tolerance": "伴侣包容",
}


def _load_cases() -> list[dict[str, Any]]:
    with CASE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rules", [])


def _find_case(case_id: str) -> dict[str, Any]:
    case = next((item for item in _load_cases() if item.get("case_id") == case_id), None)
    if not case:
        raise ValueError(f"未找到命例样本：{case_id}")
    return case


def _event_label(event_type: str) -> str:
    try:
        with (ROOT / "rules" / "monthly_event_ontology.json").open(encoding="utf-8") as f:
            ontology = json.load(f)
        return ontology.get(event_type, {}).get("label") or EVENT_LABEL_FALLBACKS.get(event_type, event_type)
    except Exception:
        return EVENT_LABEL_FALLBACKS.get(event_type, event_type)


def _build_chart_for_case(case: dict[str, Any]) -> dict[str, Any]:
    from core.bazi_engine import build_bazi_chart

    profile = dict(case.get("profile_match", {}))
    profile["name"] = case.get("profile_name", profile.get("name", ""))
    profile.setdefault("use_solar_time", False)
    return build_bazi_chart(profile)


def _system_months_for_case(case: dict[str, Any], chart: dict[str, Any]) -> list[dict[str, Any]]:
    from core.monthly_engine import analyze_monthly_fortune
    from core.monthly_event_activation_bridge import build_year_monthly_event_results
    from core.yearly_engine import analyze_yearly_fortune

    year = int(case.get("year", 2026))
    yearly = analyze_yearly_fortune(chart, year)
    monthly = analyze_monthly_fortune(chart, year)
    results = build_year_monthly_event_results(chart, monthly, yearly)
    output = []
    for item, result in zip(monthly, results):
        top_events = []
        for event in result.get("top_events", [])[:3]:
            merged_from = event.get("merged_from", []) or []
            top_events.append(
                {
                    "event_type": event.get("event_type", ""),
                    "label": event.get("label", ""),
                    "score": event.get("score", 0),
                    "trigger_count": event.get("trigger_count", 0),
                    "probability_level": event.get("probability_level", ""),
                    "merged_from": merged_from,
                    "semantic_types": sorted(set([event.get("event_type", "")] + merged_from)),
                }
            )
        output.append(
            {
                "month": item.get("month"),
                "pillar": item.get("pillar", ""),
                "ten_god": item.get("ten_god", ""),
                "top_events": top_events,
            }
        )
    return output


def _expand_system_types(months: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    direct: list[str] = []
    semantic: list[str] = []
    for month in months:
        for event in month.get("top_events", []):
            if event.get("event_type"):
                direct.append(event["event_type"])
                semantic.append(event["event_type"])
            semantic.extend(event.get("semantic_types", []))
            for merged_type in event.get("merged_from", []) or []:
                semantic.append(merged_type)
    return list(dict.fromkeys(direct)), list(dict.fromkeys(semantic))


def _semantic_match(master_event: str, system_semantic_types: list[str]) -> bool:
    related = RELATED_EVENT_GROUPS.get(master_event, {master_event})
    return bool(related & set(system_semantic_types))


def _recommend_for_miss(event_type: str, period: dict[str, Any]) -> str:
    label = _event_label(event_type)
    source_text = period.get("master_original_text", "")
    if event_type in {"social_drinking", "favor_obligation"}:
        return f"{label}：当样本出现“酒友/人情”并叠加财务或车辆信号时，提高社交资源链权重，但不要单独刷屏。"
    if event_type in {"vehicle_safety", "safety_attention", "travel_delay"}:
        return f"{label}：遇到开车、台风天、外部扰动时，应把交通安全和行程变动放入 Top 候选。"
    if event_type in {"impulsive_decision", "minor_loss", "gossip_dispute", "misunderstanding_risk"}:
        return f"{label}：将“改革三思、不要贪、小心小人”转译为小额损耗、误会和口舌风险的降级提醒。"
    if event_type in {"project_progress", "business_negotiation", "cooperation_opportunity", "business_partnership"}:
        return f"{label}：责任、新机遇、招募合作同段出现时，合作机会应进入项目/合同类候选。"
    if event_type in {"debt_borrowing", "cashflow_pressure", "investment_risk", "wealth_outflow"}:
        return f"{label}：担保、套牢、防破财应合并为现金流压力链，提高比劫+财务风险的组合权重。"
    if event_type in {"property_housing", "shop_property", "asset_purchase", "vehicle_expense", "equipment_purchase"}:
        return f"{label}：样本的“房、店、车、逢财置物”应强化为财星转实物/资产添置链。"
    if event_type in {"official_dispute", "rule_penalty", "legal_compliance"}:
        return f"{label}：把“110警告”安全翻译为规则、纠纷、处罚或合规边界，不做恐吓判断。"
    if event_type in {"relationship_progress", "partner_planning"}:
        return f"{label}：感情信号需和公司、房店车、责任压力同看，避免只输出泛化关系升温。"
    if event_type in {"family_issue", "family_responsibility"}:
        return f"{label}：近亲人事、子女事或家庭责任出现时，应和财务、业务、情绪一起看，不宜单独套家庭模板。"
    if event_type in {"sudden_change_warning"}:
        return f"{label}：把忽然变化安全转译为计划、出行、流程或规则临时转向，排序时要和110、出行或压抑感同看。"
    if event_type in {"trapped_commitment"}:
        return f"{label}：被套住需要区分资金套牢、关系拉扯和合作承诺，优先看财星、比劫、日支和忌神叠加。"
    if event_type in {"short_term_cooperation"}:
        return f"{label}：短合代表阶段性合作或试运行，不宜和长期合作混成同一类。"
    if event_type in {"female_friend_social"}:
        return f"{label}：闺蜜亲友应从同辈、桃花、人缘和年支亲友位拆来源，不只写泛化贵人。"
    if event_type in {"business_procedure_handling"}:
        return f"{label}：办业务要落到证件、审批、材料、流程和凭证，优先联动官杀与印星。"
    if event_type in {"child_family_responsibility"}:
        return f"{label}：子女事只做晚辈、家庭责任和长期规划提醒，不做绝对生育判断。"
    if event_type in {"partner_tolerance"}:
        return f"{label}：伴侣包容需要和日支、财官、食伤沟通及内耗状态共同判断。"
    if event_type in {"work_block", "delayed_issue", "overwork"}:
        return f"{label}：内耗、被困或拖住类内容要和业务推进、现金流和身体状态合并解释。"
    if event_type in {"sales_conversion", "business_cash_in", "business_partnership", "content_traffic"}:
        return f"{label}：买卖、业务和放量信号应区分成交、现金流、合作和流量，不宜只说事业机会。"
    if event_type in {"resource_connection", "referral_opportunity", "old_friend_contact", "customer_growth"}:
        return f"{label}：贵人和旧资源回流应拆来源，优先观察旧客户、转介绍、平台入口和专业建议。"
    return f"{label}：师傅样本原文“{source_text}”中出现该现实事件，建议检查其触发规则和排序权重。"


def build_master_case_calibration(case_id: str = "chen_pengshu_2026_master_monthly") -> dict[str, Any]:
    case = _find_case(case_id)
    chart = _build_chart_for_case(case)
    system_months = _system_months_for_case(case, chart)

    chart_pillars = [chart.get("pillars", {}).get(key, {}).get("pillar", "") for key in ["year", "month", "day", "hour"]]
    paper_pillars = list(reversed(case.get("bazi_pillars", [])))

    comparisons = []
    for period in case.get("monthly_periods", []):
        months = period.get("months", [])
        system_slice = [item for item in system_months if item.get("month") in months]
        direct_types, semantic_types = _expand_system_types(system_slice)
        master_types = period.get("mapped_event_types", [])
        exact_hits = [event_type for event_type in master_types if event_type in direct_types or event_type in semantic_types]
        semantic_hits = [
            event_type
            for event_type in master_types
            if event_type not in exact_hits and _semantic_match(event_type, semantic_types)
        ]
        missed = [
            event_type
            for event_type in master_types
            if event_type not in exact_hits and event_type not in semantic_hits
        ]
        coverage = (len(exact_hits) + len(semantic_hits)) / max(1, len(master_types))
        comparisons.append(
            {
                "period_id": period.get("period_id", ""),
                "months": months,
                "month_label": f"{months[0]}-{months[-1]} 月" if months else "",
                "master_original_text": period.get("master_original_text", ""),
                "confirmed_notes": period.get("confirmed_notes", []),
                "master_event_types": master_types,
                "master_event_labels": [_event_label(event_type) for event_type in master_types],
                "system_months": system_slice,
                "system_top3_event_types": direct_types,
                "system_semantic_event_types": semantic_types,
                "exact_hit_event_types": exact_hits,
                "semantic_hit_event_types": semantic_hits,
                "missed_event_types": missed,
                "coverage_rate": round(coverage, 3),
                "distilled_reasoning": period.get("distilled_reasoning", []),
                "tuning_recommendations": [_recommend_for_miss(event_type, period) for event_type in missed]
                or ["当前段落已有基本覆盖，后续只需观察排序是否贴近用户感知。"],
            }
        )

    all_missed = [event_type for item in comparisons for event_type in item["missed_event_types"]]
    average_coverage = round(
        sum(item["coverage_rate"] for item in comparisons) / max(1, len(comparisons)),
        3,
    )
    return {
        "case_id": case.get("case_id", ""),
        "profile_name": case.get("profile_name", ""),
        "year": case.get("year", 2026),
        "chart_pillars_year_month_day_hour": chart_pillars,
        "paper_pillars_right_to_left_normalized": paper_pillars,
        "pillar_order_note": "纸质盘面常见右到左展示；程序按年、月、日、时输出。",
        "system_months": system_months,
        "period_comparisons": comparisons,
        "overall_coverage": average_coverage,
        "overall": {
            "period_count": len(comparisons),
            "average_coverage_rate": average_coverage,
            "missed_event_type_count": len(set(all_missed)),
            "priority_misses": sorted(set(all_missed))[:20],
        },
    }


def _fmt_types(types: list[str]) -> str:
    if not types:
        return "无"
    return "、".join(f"{_event_label(event_type)}({event_type})" for event_type in types)


def _default_report_path(audit: dict[str, Any]) -> Path:
    case_id = audit.get("case_id", "unknown_case")
    slug = case_id.replace("_master_monthly", "")
    return REPORT_DIR / f"master_case_{slug}_calibration_audit.md"


def write_calibration_report(audit: dict[str, Any], path: Path | None = None) -> Path:
    if path is None:
        path = _default_report_path(audit)
    lines = [
        f"# {audit['profile_name']} {audit['year']} 流月样本校准审计",
        "",
        "本报告用于把现实师傅样本与系统当前 2026 流月 Top3 做逐段对比，先找命中与漏项，再决定调权方向。",
        "",
        "## 基础信息",
        f"- 样本：{audit['profile_name']}",
        f"- 年份：{audit['year']}",
        f"- 程序四柱（年/月/日/时）：{' '.join(audit['chart_pillars_year_month_day_hour'])}",
        f"- 纸质盘面四柱按右到左还原：{' '.join(audit['paper_pillars_right_to_left_normalized'])}",
        f"- 说明：{audit['pillar_order_note']}",
        "",
        "## 总体命中",
        f"- 六段平均覆盖率：{audit['overall']['average_coverage_rate']:.3f}",
        f"- 未覆盖事件类型数：{audit['overall']['missed_event_type_count']}",
        f"- 优先漏项：{_fmt_types(audit['overall']['priority_misses'])}",
        "",
        "## 系统当前 2026 每月 Top3",
    ]
    for month in audit["system_months"]:
        event_text = "、".join(
            f"{event['label']}({event['event_type']})"
            for event in month.get("top_events", [])
        )
        lines.append(
            f"- {month['month']}月 {month['pillar']} {month['ten_god']}：{event_text or '无'}"
        )

    lines.extend(["", "## 六段逐段对比"])
    for period in audit["period_comparisons"]:
        lines.extend(
            [
                "",
                f"### {period['month_label']}",
                f"- 师傅原文：{period['master_original_text']}",
                f"- 师傅事件映射：{_fmt_types(period['master_event_types'])}",
                f"- 系统 Top3：{_fmt_types(period['system_top3_event_types'])}",
                f"- 命中：{_fmt_types(period['exact_hit_event_types'])}",
                f"- 语义命中：{_fmt_types(period['semantic_hit_event_types'])}",
                f"- 漏项：{_fmt_types(period['missed_event_types'])}",
                f"- 覆盖率：{period['coverage_rate']:.3f}",
                "- 蒸馏观察：",
            ]
        )
        for item in period.get("distilled_reasoning", []):
            lines.append(f"  - {item}")
        lines.append("- 调权建议：")
        for item in period.get("tuning_recommendations", []):
            lines.append(f"  - {item}")

    lines.extend(
        [
            "",
            "## 下一步调权原则",
            "- 不把师傅样本写成硬覆盖规则，只作为排序和组合解释的校准样本。",
            "- 优先让已有候选池中的事件进入合适段落 Top3，而不是盲目扩展事件数量。",
            "- 高风险表达需要转译成用户可读的安全提醒，例如 110 对应规则边界、报警边界或合规提醒。",
            "- 若某个样本事件完全没有事件库支撑，再补事件库；已有事件则优先调触发链和排序权重。",
        ]
    )
    output = "\n".join(lines) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        return path
    except PermissionError:
        fallback = Path(tempfile.gettempdir()) / path.name
        fallback.write_text(output, encoding="utf-8")
        return fallback


def run(case_id: str = "chen_pengshu_2026_master_monthly") -> dict[str, Any]:
    audit = build_master_case_calibration(case_id)
    write_calibration_report(audit)
    return audit


if __name__ == "__main__":
    for case_id in ["chen_pengshu_2026_master_monthly", "zhou_huimin_2026_master_monthly"]:
        result = run(case_id)
        report_path = _default_report_path(result)
        print(f"已生成：{report_path}")
        print(f"平均覆盖率：{result['overall']['average_coverage_rate']:.3f}")
        print(f"漏项数量：{result['overall']['missed_event_type_count']}")
