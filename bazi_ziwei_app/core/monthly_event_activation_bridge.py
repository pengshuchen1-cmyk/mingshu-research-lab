"""Monthly event activation bridge. ASCII-only. Chinese text from JSON."""

from __future__ import annotations

import json
import os
from typing import Any

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ACTIVATION_ASSETS_CACHE: dict | None = None

def load_activation_assets(force: bool = False) -> dict:
    """Load immutable rule assets once per process, with an explicit refresh hook."""
    global _ACTIVATION_ASSETS_CACHE
    if _ACTIVATION_ASSETS_CACHE is not None and not force:
        return _ACTIVATION_ASSETS_CACHE

    base = _BASE
    assets = {}
    for name, key in [
        ("monthly_event_ontology.json", "ontology"),
        ("monthly_event_trigger_rules.json", "trigger_rules"),
        ("monthly_event_variants.json", "variants"),
    ]:
        path = os.path.join(base, "rules", name)
        try:
            with open(path, encoding="utf-8") as f:
                assets[key] = json.load(f)
        except Exception:
            assets[key] = {} if key in ("ontology", "variants") else []
    reg_path = os.path.join(base, "rules", "source_registry.json")
    try:
        with open(reg_path, encoding="utf-8") as f:
            assets["source_registry"] = json.load(f)
    except Exception:
        assets["source_registry"] = {}
    from core.bazi_constants import STEM_ELEMENTS, BRANCH_MAIN_ELEMENTS
    assets["stem_elements"] = STEM_ELEMENTS
    assets["branch_main_elements"] = BRANCH_MAIN_ELEMENTS
    _ACTIVATION_ASSETS_CACHE = assets
    return _ACTIVATION_ASSETS_CACHE


def build_month_context(chart: dict, monthly_item: dict,
                        yearly_data: dict | None = None,
                        luck_data: dict | None = None,
                        assets: dict | None = None) -> dict:
    ctx: dict[str, Any] = {}
    assets = assets or load_activation_assets()
    STE = assets.get("stem_elements", {})
    BME = assets.get("branch_main_elements", {})

    ctx["month_gan"] = monthly_item.get("gan", "")
    ctx["month_zhi"] = monthly_item.get("zhi", "")
    ctx["month_pillar"] = monthly_item.get("pillar", "")
    ctx["month_index"] = monthly_item.get("month", 0)
    ctx["target_year"] = int(yearly_data.get("year", 0) or 0) if yearly_data else 0
    ctx["month_element"] = STE.get(ctx["month_gan"], "")
    ctx["month_zhi_element"] = BME.get(ctx["month_zhi"], "")
    ctx["month_ten_god"] = monthly_item.get("ten_god", "")

    tg = ctx["month_ten_god"]
    ctx["is_wealth_month"] = tg in ("正财", "偏财")
    ctx["is_officer_month"] = tg in ("正官", "七杀")
    ctx["is_output_month"] = tg in ("食神", "伤官")
    ctx["is_resource_month"] = tg in ("正印", "偏印")
    ctx["is_peer_month"] = tg in ("比肩", "劫财")
    ctx["month_ten_god_group"] = (
        "wealth" if ctx["is_wealth_month"] else
        "officer" if ctx["is_officer_month"] else
        "output" if ctx["is_output_month"] else
        "resource" if ctx["is_resource_month"] else
        "peer" if ctx["is_peer_month"] else ""
    )

    strength = chart.get("day_master_strength", {})
    fav = set(strength.get("favorable_elements", []))
    unfav = set(strength.get("unfavorable_elements", []))
    ctx["favorable_elements"] = list(fav)
    ctx["unfavorable_elements"] = list(unfav)
    ge = ctx["month_element"]
    ze = ctx["month_zhi_element"]
    is_f = ge in fav or ze in fav
    is_u = ge in unfav or ze in unfav
    ctx["favorable_relation"] = "喜用相关" if is_f else "忌神相关" if is_u else "平稳观察"

    # Clash detection
    _P = chart.get("pillars", {})
    _BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    _LIUCHONG = [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]
    def _is_chong(b1, b2):
        return (b1, b2) in _LIUCHONG or (b2, b1) in _LIUCHONG
    
    mz = ctx["month_zhi"]
    ctx["clash_year_branch"] = _is_chong(mz, _P.get("year", {}).get("zhi", ""))
    ctx["clash_month_branch"] = _is_chong(mz, _P.get("month", {}).get("zhi", ""))
    ctx["clash_day_branch"] = _is_chong(mz, _P.get("day", {}).get("zhi", ""))
    ctx["clash_hour_branch"] = _is_chong(mz, _P.get("hour", {}).get("zhi", ""))
    ctx["clash_any"] = any([ctx["clash_year_branch"], ctx["clash_month_branch"],
                            ctx["clash_day_branch"], ctx["clash_hour_branch"]])

    # Star activation
    ctx["activate_wealth_star"] = ctx["is_wealth_month"]
    ctx["activate_officer_star"] = ctx["is_officer_month"]
    ctx["activate_output_star"] = ctx["is_output_month"]
    ctx["activate_resource_star"] = ctx["is_resource_month"]
    ctx["activate_peer_star"] = ctx["is_peer_month"]
    ctx["activate_spouse_palace"] = ctx["clash_day_branch"] or ctx["month_zhi"] in ("子","午","卯","酉")
    ctx["activate_peach_blossom"] = ctx["month_zhi"] in ("子","午","卯","酉")
    counts = chart.get("ten_god_counts", {}) or {}
    ctx["ten_god_counts"] = counts
    ctx["group_counts"] = {
        "wealth": counts.get("正财", 0) + counts.get("偏财", 0),
        "officer": counts.get("正官", 0) + counts.get("七杀", 0),
        "output": counts.get("食神", 0) + counts.get("伤官", 0),
        "resource": counts.get("正印", 0) + counts.get("偏印", 0),
        "peer": counts.get("比肩", 0) + counts.get("劫财", 0),
    }
    ctx["gender"] = (chart.get("profile", {}) or {}).get("gender", "")
    ctx["day_master"] = chart.get("day_master", "")
    ctx["day_master_element"] = STE.get(ctx["day_master"], "")
    pillars = chart.get("pillars", {})
    # Luck / year
    ctx["year_ten_god"] = ""
    ctx["year_element"] = ""
    if yearly_data:
        ctx["year_ten_god"] = yearly_data.get("ten_god", "")
        yg = yearly_data.get("gan", "")
        ctx["year_element"] = STE.get(yg, "")

    # Overstrong/weak elements
    fe = chart.get("five_elements", {})
    if fe:
        scores = [(e, float(v)) for e, v in fe.items()]
        scores.sort(key=lambda x: -x[1])
        max_s = scores[0][1] if scores else 0
        min_s = scores[-1][1] if len(scores) > 1 else 0
        ctx["overstrong_elements"] = [e for e, v in scores if v >= max_s * 0.8 and v > 0]
        ctx["weak_elements"] = [e for e, v in scores if v <= min_s * 1.2 and v > 0]
    else:
        ctx["overstrong_elements"] = []
        ctx["weak_elements"] = []

    return ctx


def match_condition(cond: dict, ctx: dict) -> dict:
    ctype = cond.get("type", "")
    value = cond.get("value", [])
    if not isinstance(value, list):
        value = [value]
    
    matched = False
    detail = ""
    
    if ctype == "ten_god":
        m_tg = ctx.get("month_ten_god", "")
        matched = m_tg in value
        if matched:
            detail = f"十神{m_tg}匹配"
    elif ctype == "favorable_relation":
        matched = ctx.get("favorable_relation", "") in value
        if matched:
            detail = f"喜忌关系匹配"
    elif ctype == "month_index":
        matched = int(ctx.get("month_index", 0) or 0) in [int(v) for v in value]
        if matched:
            detail = "流月序位匹配"
    elif ctype == "ten_god_group":
        group = ctx.get("month_ten_god_group", "")
        matched = group in value
        if matched:
            detail = f"流月十神组{group}匹配"
    elif ctype == "element":
        me = ctx.get("month_element", "")
        ze = ctx.get("month_zhi_element", "")
        matched = me in value or ze in value
        if matched:
            detail = f"五行{me or ze}匹配"
    elif ctype == "is_wealth_month":
        matched = ctx.get("is_wealth_month", False)
    elif ctype == "is_officer_month":
        matched = ctx.get("is_officer_month", False)
    elif ctype == "is_output_month":
        matched = ctx.get("is_output_month", False)
    elif ctype == "is_resource_month":
        matched = ctx.get("is_resource_month", False)
    elif ctype == "is_peer_month":
        matched = ctx.get("is_peer_month", False)
    elif ctype == "clash_any":
        matched = ctx.get("clash_any", False)
    elif ctype.startswith("clash_"):
        matched = ctx.get(ctype, False)
    elif ctype.startswith("activate_"):
        matched = ctx.get(ctype, False)
    elif ctype == "candidate_exists":
        # Will be resolved later
        matched = False
    elif ctype == "element_in":
        matched = any(e in ctx.get("month_element", "") or e in ctx.get("month_zhi_element", "")
                     for e in value)
    elif ctype == "unfavorable_any":
        ue = ctx.get("unfavorable_elements", [])
        matched = any(e in ue for e in value)
    elif ctype == "group_count_at_least":
        group_counts = ctx.get("group_counts", {})
        for item in value:
            if not isinstance(item, dict):
                continue
            group = item.get("group", "")
            min_value = float(item.get("min", 0))
            if float(group_counts.get(group, 0)) >= min_value:
                matched = True
                detail = f"原局{group}组数量达到{min_value:g}"
                break
    elif ctype == "element_strength":
        roles = set(value)
        if "overstrong" in roles and ctx.get("month_element") in ctx.get("overstrong_elements", []):
            matched = True
            detail = "流月天干五行触发偏旺元素"
        elif "weak" in roles and ctx.get("month_zhi_element") in ctx.get("weak_elements", []):
            matched = True
            detail = "流月地支五行触发偏弱元素"
    elif ctype == "branch_in":
        matched = ctx.get("month_zhi", "") in value
        if matched:
            detail = f"地支{ctx.get('month_zhi', '')}匹配"
    elif ctype == "gender":
        matched = ctx.get("gender", "") in value
        if matched:
            detail = "性别取象匹配"
    elif ctype == "day_master_element":
        matched = ctx.get("day_master_element", "") in value
        if matched:
            detail = "日主五行匹配"
    
    evidence_text = cond.get("evidence_text", "")
    weight = cond.get("weight", 1)
    
    return {
        "matched": matched,
        "detail": detail or evidence_text,
        "type": ctype,
        "value": value,
        "weight": weight,
        "source_ids": cond.get("source_ids", []),
        "source_relevance": cond.get("source_relevance", 0.7),
    }


def activate_events_by_rules(ctx: dict, assets: dict) -> list[dict]:
    candidates = []
    rules = assets.get("trigger_rules", [])
    ontology = assets.get("ontology", {})

    for rule in rules:
        et = rule.get("target_event_type", "")
        min_count = rule.get("min_trigger_count", 2)
        conditions = rule.get("trigger_conditions", [])
        if not conditions:
            continue

        matched_results = []
        for cond in conditions:
            result = match_condition(cond, ctx)
            if result.get("matched"):
                matched_results.append(result)

        if len(matched_results) >= min_count:
            total_weight = sum(r.get("weight", 1) for r in matched_results)
            seed = f"{et}:{ctx.get('month_index', 0)}:{ctx.get('day_master', '')}:{ctx.get('month_pillar', '')}"
            tie_breaker = sum(ord(ch) for ch in seed) % 9
            score = min(88, 20 + total_weight * 10 + tie_breaker)
            evidence_list = []
            source_id_set = set()
            for mr in matched_results:
                evidence_list.append({
                    "type": mr.get("type", ""),
                    "value": mr.get("value", ""),
                    "detail": mr.get("detail", ""),
                    "source_ids": mr.get("source_ids", []),
                    "source_relevance": mr.get("source_relevance", 0.7),
                })
                for sid in mr.get("source_ids", []):
                    source_id_set.add(sid)
            rule_sids = rule.get("source_ids", [])
            for sid in rule_sids:
                source_id_set.add(sid)

            candidate = {
                "event_type": et,
                "score": score,
                "trigger_count": len(matched_results),
                "evidence": evidence_list,
                "source_ids": list(source_id_set) if source_id_set else rule_sids,
                "matched_conditions": matched_results,
                "from_bridge": True,
            }
            candidates.append(candidate)

    candidates.sort(key=lambda x: -x["score"])
    return candidates


def _select_variant(event_type: str, evidence_list: list, variants_db: dict, month_index: int = 0) -> dict | None:
    evars = variants_db.get(event_type, [])
    if not evars:
        return None
    evidence_texts = []
    for ev in evidence_list:
        d = ev.get("detail", "")
        if d:
            evidence_texts.append(d)
        t = ev.get("type", "")
        if t:
            evidence_texts.append(t)
    big_text = " ".join(evidence_texts)
    for v in evars:
        pat = v.get("trigger_pattern", [])
        if pat and any(p in big_text for p in pat):
            return v
    if not evars:
        return None
    if len(evars) == 1 or not evidence_list:
        return evars[0]
    # Distribute variants using evidence + month_index to ensure month-to-month variation
    seed_str = event_type + str(month_index) + str(len(evidence_list)) + "".join(str(e.get("type","")) for e in evidence_list[:3])
    idx = sum(ord(c) for c in seed_str) % len(evars)
    return evars[idx]


def _source_titles_from_registry(sids: list, registry: dict) -> list:
    titles = []
    for sid in sids:
        entry = registry.get(sid, {})
        t = entry.get("title", "")
        if t:
            titles.append(t)
    return titles


def _evidence_dimensions(evidence_list: list[dict]) -> set[str]:
    dimensions: set[str] = set()
    for item in evidence_list:
        etype = item.get("type", "")
        if etype in ("ten_god", "ten_god_group") or etype.startswith("is_") or etype.startswith("activate_"):
            dimensions.add("十神")
        if etype in ("favorable_relation", "element", "element_in", "element_strength", "unfavorable_any", "day_master_element"):
            dimensions.add("五行喜忌")
        if etype.startswith("clash_") or etype in ("branch_in",):
            dimensions.add("宫位/地支")
        if etype in ("group_count_at_least",):
            dimensions.add("原局结构")
        if etype in ("month_index",):
            dimensions.add("流月节奏")
    return dimensions


def _downgrade_confidence(level: str) -> str:
    if level == "high":
        return "medium"
    if level == "medium":
        return "low"
    return "low"


def _source_specificity_weight(value: str) -> float:
    weights = {
        "broad": 0.2,
        "classic": 0.35,
        "chapter": 0.55,
        "rule": 0.75,
        "case": 0.85,
    }
    return weights.get(str(value or "broad"), 0.2)


def _collect_candidate_source_ids(cand: dict) -> list[str]:
    source_ids = list(cand.get("source_ids", []) or [])
    for item in cand.get("evidence", []) or []:
        source_ids.extend(item.get("source_ids", []) or [])
    seen = set()
    unique = []
    for sid in source_ids:
        if sid not in seen:
            unique.append(sid)
            seen.add(sid)
    return unique


def _evaluate_source_confidence(cand: dict, onto: dict, source_registry: dict | None = None) -> dict:
    registry = source_registry or {}
    source_ids = _collect_candidate_source_ids(cand)
    category = onto.get("category", "")
    if not source_ids:
        return {
            "source_confidence_score": 0.0,
            "source_confidence_reasons": ["未命中来源依据。"],
            "source_has_specific_support": False,
            "source_has_category_match": False,
        }

    relevance_by_sid: dict[str, float] = {}
    for sid in cand.get("source_ids", []) or []:
        relevance_by_sid[sid] = max(relevance_by_sid.get(sid, 0.0), 0.55)
    for item in cand.get("evidence", []) or []:
        relevance = float(item.get("source_relevance", 0.7) or 0.7)
        for sid in item.get("source_ids", []) or []:
            relevance_by_sid[sid] = max(relevance_by_sid.get(sid, 0.0), relevance)

    scores = []
    has_specific = False
    has_category_match = False
    for sid in source_ids:
        entry = registry.get(sid, {})
        authority = float(entry.get("authority_weight", 0.55) or 0.55)
        specificity = str(entry.get("specificity", "broad") or "broad")
        domains = entry.get("domains", []) or entry.get("used_for", []) or []
        penalty = float(entry.get("broadness_penalty", 0.25 if specificity == "broad" else 0) or 0)
        if specificity in {"chapter", "rule", "case"}:
            has_specific = True
        if category and category in domains:
            has_category_match = True
        score = authority * 0.65 + _source_specificity_weight(specificity) * 0.35 - penalty
        if category and category in domains:
            score += 0.1
        score *= max(0.1, min(1.0, relevance_by_sid.get(sid, 0.55)))
        scores.append(max(0.0, min(1.0, score)))

    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
    reasons = [f"来源置信分：{avg_score}"]
    if not has_specific:
        reasons.append("来源多为宽泛经典或整理资料。")
    if category and not has_category_match:
        reasons.append("来源领域与事件类别未明确匹配。")
    return {
        "source_confidence_score": avg_score,
        "source_confidence_reasons": reasons,
        "source_has_specific_support": has_specific,
        "source_has_category_match": has_category_match,
    }


def _evaluate_event_confidence(
    cand: dict,
    onto: dict,
    ctx: dict | None = None,
    source_registry: dict | None = None,
) -> dict:
    evidence = cand.get("evidence", []) or []
    trigger_count = int(cand.get("trigger_count", 0) or len(evidence))
    dimensions = _evidence_dimensions(evidence)
    has_chain_template = bool(onto.get("traditional_basis") or onto.get("confidence_basis"))
    source_confidence = _evaluate_source_confidence(cand, onto, source_registry)

    if trigger_count >= 4 and len(dimensions) >= 3:
        level = "high"
    elif trigger_count >= 3:
        level = "medium"
    else:
        level = "low"

    downgrade_reasons: list[str] = []
    if ctx and ctx.get("favorable_relation") == "忌神相关":
        downgrade_reasons.append("忌神参与较重，事件结果需要降级观察。")
    if len(dimensions) <= 1:
        downgrade_reasons.append("证据集中在单一维度，不能直接放大判断。")
    if has_chain_template and "宫位/地支" not in dimensions and trigger_count < 4:
        downgrade_reasons.append("缺少宫位或地支触发，现实落点仍需观察。")
    if has_chain_template and trigger_count < int(onto.get("required_evidence_count", 2) or 2):
        downgrade_reasons.append("命中证据少于该事件要求。")
    if level == "high" and not source_confidence["source_has_specific_support"]:
        downgrade_reasons.append("来源过于宽泛，不能支撑高置信事件。")
    if level == "high" and onto.get("category") and not source_confidence["source_has_category_match"]:
        downgrade_reasons.append("来源领域与事件类别匹配不足。")

    anti_triggers = onto.get("anti_triggers", []) or []
    if ctx and anti_triggers:
        anti_text = " ".join(str(x) for x in anti_triggers)
        if "忌神" in anti_text and ctx.get("favorable_relation") == "忌神相关":
            downgrade_reasons.append("命中反向条件：忌神参与。")
        if "冲克" in anti_text and ctx.get("clash_any"):
            downgrade_reasons.append("命中反向条件：冲动较明显。")

    if downgrade_reasons:
        level = _downgrade_confidence(level)

    return {
        "confidence_level": level,
        "confidence_dimensions": sorted(dimensions),
        "confidence_reasons": [
            f"命中{trigger_count}条证据",
            f"证据维度：{'、'.join(sorted(dimensions)) or '暂无明确维度'}",
            *source_confidence["source_confidence_reasons"],
        ],
        "downgrade_reasons": downgrade_reasons,
        "source_confidence_score": source_confidence["source_confidence_score"],
        "source_has_specific_support": source_confidence["source_has_specific_support"],
        "source_has_category_match": source_confidence["source_has_category_match"],
    }


def _ctx_group(ctx: dict | None, group: str) -> float:
    if not ctx:
        return 0
    return float((ctx.get("group_counts", {}) or {}).get(group, 0) or 0)


def _infer_nobleman_subtypes(ctx: dict | None, evidence_list: list[dict]) -> list[str]:
    if not ctx:
        return []
    subtypes: list[str] = []
    if ctx.get("is_resource_month") or _ctx_group(ctx, "resource") >= 2:
        if ctx.get("clash_year_branch"):
            subtypes.append("长辈贵人")
        if ctx.get("clash_month_branch"):
            subtypes.append("上级贵人")
        subtypes.extend(["专业人士贵人", "平台贵人"])
    if ctx.get("is_peer_month") or _ctx_group(ctx, "peer") >= 2:
        subtypes.append("同辈贵人")
    if ctx.get("is_wealth_month") or _ctx_group(ctx, "wealth") >= 2:
        subtypes.append("客户贵人")
    if ctx.get("is_officer_month") or _ctx_group(ctx, "officer") >= 2:
        subtypes.append("上级贵人")
    if ctx.get("is_output_month") or _ctx_group(ctx, "output") >= 2:
        subtypes.append("旧关系贵人")
    if ctx.get("activate_spouse_palace") or ctx.get("clash_day_branch"):
        subtypes.append("伴侣/合作贵人")
    if ctx.get("clash_year_branch"):
        subtypes.append("家庭贵人")
    if ctx.get("favorable_relation") == "喜用相关" and not subtypes:
        subtypes.append("暗中贵人")

    seen = set()
    unique = []
    for item in subtypes:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique[:3]


def _build_user_visible_basis(onto: dict, cand: dict, confidence: dict, subtypes: list[str]) -> str:
    if onto.get("user_visible_basis"):
        text = onto.get("user_visible_basis", "")
    else:
        text = onto.get("basis", "") or "该事件由流月、喜忌和命盘结构共同触发。"
    dims = "、".join(confidence.get("confidence_dimensions", []))
    if dims:
        text = f"{text} 本次主要参考{dims}。"
    if subtypes:
        text = f"{text} 当前更偏向：{'、'.join(subtypes)}。"
    return text


def merge_related_event_clusters(events: list[dict]) -> list[dict]:
    """Merge repeated signals into fewer user-facing events."""
    if not events:
        return []

    def _specific_cluster_type(default_type: str, cluster_types: set[str]) -> str:
        if default_type == "expense_pressure_cluster":
            if cluster_types & {"vehicle_expense", "vehicle_repair"}:
                return "expense_vehicle_cluster"
            if cluster_types & {"home_repair", "repair_expense", "equipment_purchase"}:
                return "expense_repair_cluster"
            if cluster_types & {"human_cost", "social_spending", "gift_expense"}:
                return "expense_social_cluster"
            if cluster_types & {"cashflow_pressure", "debt_borrowing", "debt_loss"}:
                return "expense_cashflow_cluster"
            if cluster_types & {"medical_expense_signal"}:
                return "expense_health_cluster"
        if default_type == "contract_boundary_cluster":
            if cluster_types & {"cooperation_boundary", "business_partnership", "business_negotiation"}:
                return "contract_cooperation_cluster"
            if cluster_types & {"license_document", "tax_invoice", "insurance_claim", "legal_compliance"}:
                return "contract_compliance_cluster"
            if cluster_types & {"approval_process", "document_error", "contract_document"}:
                return "contract_document_cluster"
        if default_type == "relationship_pressure_cluster":
            if cluster_types & {"family_pressure"}:
                return "relationship_family_cluster"
            if cluster_types & {"misunderstanding", "relationship_conflict", "value_conflict"}:
                return "relationship_communication_cluster"
            if cluster_types & {"emotional_distance", "breakup_risk_signal"}:
                return "relationship_cooling_cluster"
            if cluster_types & {"old_contact"}:
                return "relationship_old_contact_cluster"
        return default_type
    clusters = [
        {
            "types": {
                "old_friend_contact", "social_drinking", "networking",
                "resource_connection", "referral_opportunity", "favor_obligation",
            },
            "event_type": "social_resource_cluster",
            "label": "同辈圈层或社交场景带来资源线索",
            "category": "贵人与资源",
            "one_line": "朋友、饭局、旧关系或转介绍信号同时出现时，更适合合并观察为一条资源线索。",
            "advice": "可以赴约和沟通，但要把金额、责任、时间表和后续成本说清楚。",
            "manifestations": ["朋友组局", "饭局中出现合作线索", "旧关系带来资源入口"],
            "risks": ["人情成本增加", "口头承诺多", "边界不清"],
        },
        {
            "types": {
                "wealth_outflow", "vehicle_expense", "vehicle_repair", "home_repair",
                "repair_expense", "equipment_purchase", "human_cost", "social_spending",
                "gift_expense", "family_expense", "medical_expense_signal", "cashflow_pressure",
            },
            "event_type": "expense_pressure_cluster",
            "label": "现实支出压力增加",
            "category": "财务支出",
            "one_line": "多类支出信号同时出现时，更适合合并观察为现实支出压力，而不是拆成多条重复提醒。",
            "advice": "先列出必要支出、可延后支出和人情支出，金额较大的事项建议留凭证并重新排预算。",
            "manifestations": ["车辆或设备费用", "房屋维修", "人情礼金", "现金流紧张"],
            "risks": ["预算超支", "隐藏成本", "分账边界不清"],
        },
        {
            "types": {
                "contract_document", "approval_process", "document_error", "policy_change",
                "legal_compliance", "license_document", "tax_invoice", "cooperation_boundary",
                "business_partnership", "business_negotiation",
            },
            "event_type": "contract_boundary_cluster",
            "label": "合作规则与边界需要重新确认",
            "category": "合同法务",
            "one_line": "合同、审批、口头承诺或合作边界同时被引动时，重点不是多签文件，而是先把规则说清楚。",
            "advice": "建议把金额、期限、责任人、违约处理和口头承诺写进文字，必要时请专业人士审一遍。",
            "manifestations": ["合同条款修改", "审批延迟", "合作边界不清", "材料证件遗漏"],
            "risks": ["口头承诺不稳", "合作方变卦", "责任归属不清"],
        },
        {
            "types": {
                "emotional_distance", "misunderstanding", "family_pressure",
                "relationship_conflict", "value_conflict", "breakup_risk_signal",
                "cooperation_boundary", "old_contact",
            },
            "event_type": "relationship_pressure_cluster",
            "label": "关系沟通与外部压力增加",
            "category": "感情婚恋",
            "one_line": "关系冷淡、误会解释、家庭意见或边界议题同时出现时，更适合合并看成关系压力上升。",
            "advice": "建议先把具体问题说清楚，不把工作、金钱或家庭压力全部混进情绪里。",
            "manifestations": ["沟通误会", "家庭意见影响感情", "关系冷淡", "边界不清"],
            "risks": ["反复猜测", "第三方干扰", "金钱或现实安排引发分歧"],
        },
    ]

    merged_events: list[dict] = []
    consumed: set[str] = set()

    for spec in clusters:
        cluster = [ev for ev in events if ev.get("event_type") in spec["types"]]
        if len(cluster) < 2:
            continue
        best = sorted(cluster, key=lambda ev: (-float(ev.get("score", 0) or 0), ev.get("event_type", "")))[0]
        cluster_types = {ev.get("event_type", "") for ev in cluster}
        merged = dict(best)
        merged.update({
            "event_type": _specific_cluster_type(spec["event_type"], cluster_types),
            "label": spec["label"],
            "category": spec["category"],
            "one_line": spec["one_line"],
            "advice": spec["advice"],
            "merged_from": [ev.get("event_type", "") for ev in cluster],
            "possible_sources": [ev.get("label", "") for ev in cluster if ev.get("label")],
            "possible_manifestations": spec["manifestations"],
            "risk_points": spec["risks"],
            "trigger_count": max(int(ev.get("trigger_count", 0) or 0) for ev in cluster),
            "evidence": sum((ev.get("evidence", []) for ev in cluster), [])[:8],
        })
        merged_events.append(merged)
        consumed.update(ev.get("event_type", "") for ev in cluster)

    if not merged_events:
        return events

    result = []
    inserted = False
    for ev in events:
        et = ev.get("event_type", "")
        if et in consumed:
            if not inserted:
                result.extend(merged_events)
                inserted = True
            continue
        result.append(ev)
    if not inserted:
        result.extend(merged_events)
    return result


def _enrich_candidate(cand: dict, ontology: dict, variant: dict | None,
                      source_registry: dict, ctx: dict | None = None) -> dict:
    et = cand.get("event_type", "")
    onto = ontology.get(et, {})
    label = onto.get("label", et)
    cat = onto.get("category", "")

    pl = "需观察"
    sc = cand.get("score", 25)
    if sc >= 60:
        pl = "较高"
    elif sc >= 35:
        pl = "中等"

    one_line = ""
    signals = []
    risks = []
    advice = ""
    if variant:
        one_line = variant.get("one_line", onto.get("safe_expression", ""))
        signals = variant.get("real_world_signals", [])
        risks = variant.get("risk_points", [])
        advice = variant.get("advice", onto.get("safe_expression", ""))
    else:
        one_line = onto.get("safe_expression", "")
        signals = onto.get("possible_real_world_forms", [])
        risks = onto.get("risk_points", [])
        advice = onto.get("safe_expression", "")

    sids = cand.get("source_ids", [])
    stitles = _source_titles_from_registry(sids, source_registry)
    confidence = _evaluate_event_confidence(cand, onto, ctx, source_registry)
    if confidence["confidence_level"] == "high":
        pl = "较高"
    elif confidence["confidence_level"] == "medium":
        pl = "中等"
    elif onto.get("traditional_basis"):
        pl = "轻度观察"

    subtypes = _infer_nobleman_subtypes(ctx, cand.get("evidence", [])) if et in {
        "nobleman_help", "mentor_advice", "resource_connection", "referral_opportunity",
        "platform_support", "team_support", "family_support", "hidden_help",
    } else []
    if subtypes:
        source_text = "、".join(subtypes)
        one_line = f"{subtypes[0]}信号较明显，可重点观察{source_text}带来的提醒、牵线或资源入口。"
        advice = "建议先确认对方能提供什么、需要你承担什么，并把金额、时间、责任和人情边界说清楚。"

    return {
        "event_type": et,
        "label": label,
        "category": cat,
        "probability_level": pl,
        "score": sc,
        "trigger_count": cand.get("trigger_count", 0),
        "evidence": cand.get("evidence", []),
        "one_line": one_line,
        "real_world_signals": signals,
        "possible_manifestations": signals[:3],
        "risk_points": risks,
        "basis": onto.get("basis", ""),
        "advice": advice,
        "source_ids": sids,
        "source_titles": stitles,
        "traditional_basis": onto.get("traditional_basis", {}),
        "structure_basis": onto.get("structure_basis", {}),
        "palace_basis": onto.get("palace_basis", {}),
        "modern_mapping": onto.get("modern_mapping", {}),
        "confidence_basis": onto.get("confidence_basis", {}),
        "anti_triggers": onto.get("anti_triggers", []),
        "user_visible_basis": _build_user_visible_basis(onto, cand, confidence, subtypes),
        "required_evidence_count": onto.get("required_evidence_count", 2),
        "subtype_rules": onto.get("subtype_rules", {}),
        "subtype_candidates": subtypes,
        "subtype_label": subtypes[0] if subtypes else "",
        **confidence,
        "from_bridge": True,
    }


def merge_events(base_events: list[dict], bridge_candidates: list[dict],
                 limit: int = 3, ctx: dict | None = None,
                 assets: dict | None = None) -> list[dict]:
    if assets is None:
        assets = load_activation_assets()
    ont = assets.get("ontology", {})
    vdb = assets.get("variants", {})
    sreg = assets.get("source_registry", {})
    
    enriched = []
    for c in bridge_candidates:
        if c.get("trigger_count", 0) >= 2:
            v = _select_variant(c.get("event_type", ""), c.get("evidence", []), vdb, ctx.get("month_index", 0) if ctx else 0)
            enriched.append(_enrich_candidate(c, ont, v, sreg, ctx))
    
    seen_types = set()
    merged = []
    for ev in base_events:
        merged.append(ev)
        seen_types.add(ev.get("event_type", ""))
    
    for be in enriched:
        et = be.get("event_type", "")
        if et in seen_types or len(merged) >= limit:
            continue
        merged.append(be)
        seen_types.add(et)
    
    cat_count = {}
    final = []
    for ev in merged:
        cat = ev.get("category", "")
        cat_count[cat] = cat_count.get(cat, 0) + 1
        if cat in ("健康身体", "交通车辆") and cat_count[cat] > 1:
            continue
        final.append(ev)
    return final[:limit]


def _select_diverse_events(events: list[dict], limit: int = 5) -> list[dict]:
    """Pick evidence-backed events with category diversity in the Top 3."""
    events = merge_related_event_clusters(events)
    seen_types = set()
    selected = []
    cat_count: dict[str, int] = {}
    sorted_events = sorted(
        events,
        key=lambda ev: (
            -float(ev.get("score", 0) or 0),
            -int(ev.get("trigger_count", 0) or 0),
            ev.get("event_type", ""),
        ),
    )
    for ev in sorted_events:
        et = ev.get("event_type", "")
        if not et or et in seen_types:
            continue
        if ev.get("traditional_basis") and ev.get("confidence_level") == "low":
            continue
        cat = ev.get("category", "")
        if cat in ("交通车辆", "健康身体", "健康状态") and cat_count.get(cat, 0) >= 1:
            continue
        if len(selected) < 3 and cat_count.get(cat, 0) >= 1:
            continue
        selected.append(ev)
        seen_types.add(et)
        cat_count[cat] = cat_count.get(cat, 0) + 1
        if len(selected) >= limit:
            return selected
    for ev in sorted_events:
        et = ev.get("event_type", "")
        if not et or et in seen_types:
            continue
        cat = ev.get("category", "")
        if cat in ("交通车辆", "健康身体", "健康状态") and cat_count.get(cat, 0) >= 1:
            continue
        selected.append(ev)
        seen_types.add(et)
        cat_count[cat] = cat_count.get(cat, 0) + 1
        if len(selected) >= limit:
            break
    return selected[:limit]


def infer_monthly_likely_events_full(
    chart: dict, monthly_item: dict,
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> dict:
    from core.monthly_event_inference_engine import infer_monthly_likely_events_enhanced
    base_result = infer_monthly_likely_events_enhanced(chart, monthly_item, yearly_data, luck_data)
    assets = load_activation_assets()
    ctx = build_month_context(chart, monthly_item, yearly_data, luck_data, assets)
    bridge_candidates = activate_events_by_rules(ctx, assets)
    best_by_type: dict[str, dict] = {}
    for cand in bridge_candidates:
        event_type = cand.get("event_type", "")
        if not event_type:
            continue
        old = best_by_type.get(event_type)
        if old is None or float(cand.get("score", 0) or 0) > float(old.get("score", 0) or 0):
            best_by_type[event_type] = cand
    bridge_candidates = sorted(best_by_type.values(), key=lambda item: -float(item.get("score", 0) or 0))
    
    base_events = base_result.get("top_events", [])
    base_types = {e.get("event_type", "") for e in base_events if e.get("event_type")}
    ont = assets.get("ontology", {})
    vdb = assets.get("variants", {})
    sreg = assets.get("source_registry", {})
    
    enriched = []
    for b in bridge_candidates:
        if b.get("trigger_count", 0) >= 2 and b.get("event_type") not in base_types:
            v = _select_variant(b["event_type"], b.get("evidence", []), vdb, ctx.get("month_index", 0) if ctx else 0)
            ev = _enrich_candidate(b, ont, v, sreg, ctx)
            if ev.get("event_type"):
                enriched.append(ev)

    final = _select_diverse_events(enriched, limit=5)
    if len(final) < 3:
        final = _select_diverse_events(final + list(base_events), limit=5)
    base_result["top_events"] = final
    return base_result
# ====== v1.0.3-C 桥接层已激活 ======


def build_year_monthly_event_results(chart: dict, monthly_data: list, yearly_data=None, luck_data=None) -> list:
    from core.monthly_event_inference_engine import postprocess_monthly_events

    results = []
    for item in monthly_data:
        r = infer_monthly_likely_events_full(chart, item, yearly_data, luck_data)
        results.append(r)
    processed = postprocess_monthly_events(results)
    for result in processed:
        if not isinstance(result, dict):
            continue
        result.pop("bridge_events", None)
        result.pop("event_score_map", None)
        result.pop("month_unique_triggers", None)
    return processed

BRIDGE_VERSION = "1.0.3-C"
BRIDGE_ACTIVE = True
