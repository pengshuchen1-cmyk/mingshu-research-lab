"""八字合婚/合盘匹配分析 v1.3-A — 增强版。

新增维度：天干五合、纳音配对、喜用神互补、大运同步性、时支关系
总分保持 100 分（重分配权重）
"""

from __future__ import annotations

from core.bazi_constants import STEM_ELEMENTS, GENERATING, CONTROLLING, NAYIN_ELEMENT
from core.ten_gods import get_ten_god

BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]

BRANCH_LIUHE = frozenset({
    frozenset(("子","丑")), frozenset(("寅","亥")), frozenset(("卯","戌")),
    frozenset(("辰","酉")), frozenset(("巳","申")), frozenset(("午","未")),
})
BRANCH_SANHE = frozenset({
    frozenset(("申","子","辰")), frozenset(("亥","卯","未")),
    frozenset(("寅","午","戌")), frozenset(("巳","酉","丑")),
})
BRANCH_LIUCHONG = frozenset({
    frozenset(("子","午")), frozenset(("丑","未")), frozenset(("寅","申")),
    frozenset(("卯","酉")), frozenset(("辰","戌")), frozenset(("巳","亥")),
})
BRANCH_LIUHAI = frozenset({
    frozenset(("子","未")), frozenset(("丑","午")), frozenset(("寅","巳")),
    frozenset(("卯","辰")), frozenset(("申","亥")), frozenset(("酉","戌")),
})

# 天干五合：甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
HEAVENLY_HE = {"甲":"己","己":"甲","乙":"庚","庚":"乙","丙":"辛","辛":"丙","丁":"壬","壬":"丁","戊":"癸","癸":"戊"}
HEAVENLY_HE_ELEMENT = {("甲","己"):"土", ("乙","庚"):"金", ("丙","辛"):"水", ("丁","壬"):"木", ("戊","癸"):"火",
                       ("己","甲"):"土", ("庚","乙"):"金", ("辛","丙"):"水", ("壬","丁"):"木", ("癸","戊"):"火"}

SOURCE_IDS = ["yuanhai_ziping", "sanming_tonghui", "mingli_tanyuan"]
SOURCE_TITLES = ["《渊海子平》", "《三命通会》", "《命理探源》"]


def analyze_compatibility(chart1: dict, chart2: dict, luck_data1: dict | None = None, luck_data2: dict | None = None) -> dict:
    """增强版合婚匹配分析（总分100分）。"""
    results = {"overall_score": 0, "dimensions": [], "summary": "", "level": "", "key_cautions": [], "source_ids": SOURCE_IDS, "source_titles": SOURCE_TITLES, "basis": ""}
    cautions = []

    def _add(entry: dict):
        results["dimensions"].append(entry)

    p1 = chart1.get("pillars", {})
    p2 = chart2.get("pillars", {})

    # 1. 年支关系 (8分)
    yz1, yz2 = p1.get("year", {}).get("zhi", ""), p2.get("year", {}).get("zhi", "")
    if yz1 and yz2:
        sc, txt, lab = _analyze_branch_pair(yz1, yz2, "年支")
        _add({"label": "年支关系", "score": round(sc * 8 / 15), "max_score": 8, "text": txt, "detail": lab})

    # 2. 月支关系 (5分)
    mz1, mz2 = p1.get("month", {}).get("zhi", ""), p2.get("month", {}).get("zhi", "")
    if mz1 and mz2:
        sc, txt, lab = _analyze_branch_pair(mz1, mz2, "月支")
        _add({"label": "月支关系", "score": round(sc * 5 / 10), "max_score": 5, "text": txt, "detail": lab})

    # 3. 日支关系 (15分)
    dz1, dz2 = p1.get("day", {}).get("zhi", ""), p2.get("day", {}).get("zhi", "")
    if dz1 and dz2:
        sc, txt, lab = _analyze_branch_pair(dz1, dz2, "日支（夫妻宫）")
        _add({"label": "日支（夫妻宫）", "score": round(sc * 15 / 20), "max_score": 15, "text": txt, "detail": lab})
        if sc <= 5:
            cautions.append(f"日支（夫妻宫）{lab}，关系核心层面存在冲克，需要更多沟通和包容。")

    # 4. 时支关系 (8分 NEW)
    hz1, hz2 = p1.get("hour", {}).get("zhi", ""), p2.get("hour", {}).get("zhi", "")
    if hz1 and hz2:
        sc, txt, lab = _analyze_branch_pair(hz1, hz2, "时支")
        _add({"label": "时支关系", "score": round(sc * 8 / 15), "max_score": 8, "text": txt, "detail": lab})

    # 5. 日主五行 (15分)
    dm1, dm2 = chart1.get("day_master", ""), chart2.get("day_master", "")
    if dm1 and dm2:
        el1, el2 = STEM_ELEMENTS.get(dm1, ""), STEM_ELEMENTS.get(dm2, "")
        if el1 and el2:
            sc, txt = _analyze_element_pair(el1, el2, dm1, dm2)
            _add({"label": "日主五行", "score": round(sc * 15 / 25), "max_score": 15, "text": txt, "detail": f"甲方：{dm1}({el1})，乙方：{dm2}({el2})"})
            if sc <= 12:
                cautions.append(f"日主五行{el1}与{el2}存在克制，双方在核心决策上的方式差异较大，宜增加尊重与协调。")

    # 6. 天干五合 (10分 NEW)
    gan_score, gan_detail = _analyze_heavenly_stems(p1, p2)
    _add({"label": "天干五合", "score": gan_score, "max_score": 10, "text": gan_detail, "detail": "年/月/日/时天干五合检查"})

    # 7. 纳音配对 (8分 NEW)
    nayin_score, nayin_detail = _analyze_nayin(p1, p2)
    _add({"label": "纳音配对", "score": nayin_score, "max_score": 8, "text": nayin_detail, "detail": "年柱纳音五行生克"})

    # 8. 喜用神互补 (10分 NEW)
    fav1 = set(chart1.get("day_master_strength", {}).get("favorable_elements", []))
    fav2 = set(chart2.get("day_master_strength", {}).get("favorable_elements", []))
    fe1_set = set(chart1.get("five_elements", {}).keys())
    fe2_set = set(chart2.get("five_elements", {}).keys())
    fav_score, fav_detail = _analyze_favorable_complement(fav1, fav2, fe1_set, fe2_set)
    _add({"label": "喜用神互补", "score": fav_score, "max_score": 10, "text": fav_detail, "detail": "一方喜用是否为对方旺五行"})
    if fav_score <= 4:
        cautions.append("双方喜用五行互补性不足，在生活节奏和支持方式上可能需要更多主动理解。")

    # 9. 五行互补 (10分)
    fe1, fe2 = chart1.get("five_elements", {}), chart2.get("five_elements", {})
    if fe1 and fe2:
        comp_score, comp_detail = _analyze_element_complement_v2(fe1, fe2)
        _add({"label": "五行互补", "score": round(comp_score * 10 / 20), "max_score": 10, "text": comp_detail, "detail": ""})

    # 10. 十神互参 (5分)
    tg1, tg2 = chart1.get("ten_god_counts", {}), chart2.get("ten_god_counts", {})
    tg_score = _analyze_ten_god_compatibility(tg1, tg2, dm1, dm2)
    _add({"label": "十神互参", "score": round(tg_score * 5 / 10), "max_score": 5, "text": "十神结构和价值观互补程度。", "detail": ""})

    # 11. 大运同步性 (6分 NEW)
    da_score, da_detail = _analyze_daxian_sync(luck_data1, luck_data2, chart1, chart2)
    _add({"label": "大运同步性", "score": da_score, "max_score": 6, "text": da_detail, "detail": "当前大运阶段协调性"})

    # 总分
    total = min(100, sum(d["score"] for d in results["dimensions"]))
    results["overall_score"] = total
    results["key_cautions"] = cautions[:5]

    # 综合评语
    if total >= 80:
        results["summary"] = "双方八字匹配度高，天干地支多组合关系，五行互补良好，命理层面和谐融洽。"
        results["level"] = "上佳"
    elif total >= 65:
        results["summary"] = "双方八字匹配度较高，关键维度上有互补或协调，少数方面需用心磨合。"
        results["level"] = "良好"
    elif total >= 50:
        results["summary"] = "双方八字匹配度中等，存在互补面也有冲克面，需要在理解和包容上多下工夫。"
        results["level"] = "中等"
    elif total >= 35:
        results["summary"] = "双方八字匹配度偏低，关键维度上差异较大，需要更多的包容、沟通和共同努力。"
        results["level"] = "较低"
    else:
        results["summary"] = "双方八字匹配度较低，在多个重要维度上存在冲突或差异，需要慎重评估和深度磨合。"
        results["level"] = "需关注"

    results["basis"] = "基于《渊海子平》《三命通会》《命理探源》的八字合婚体系，从地支六冲六合、天干五合、纳音五行、喜用互补、大运同步等维度综合评判。"
    
    # 命主特质 + 合/不合分析 + 建议
    results["person_a"] = _describe_person(chart1)
    results["person_b"] = _describe_person(chart2)
    results["match_reasons"] = _generate_match_reasons(results["dimensions"], chart1, chart2)
    results["conflict_reasons"] = _generate_conflict_reasons(results["dimensions"], chart1, chart2)
    results["advice_list"] = _generate_compatibility_advice(results["dimensions"], chart1, chart2)
    return results


def _analyze_branch_pair(z1: str, z2: str, label: str) -> tuple:
    pair = frozenset((z1, z2))
    if pair in BRANCH_LIUHE:
        return (15, f"{label}{z1}与{z2}形成六合，良配信号，相处融洽。", f"{z1}与{z2}六合")
    for ss in BRANCH_SANHE:
        if z1 in ss and z2 in ss:
            return (12, f"{label}{z1}与{z2}形成三合，关系和谐。", f"{z1}与{z2}三合")
    if pair in BRANCH_LIUCHONG:
        return (5, f"{label}{z1}与{z2}六冲，需多加磨合和包容。", f"{z1}与{z2}六冲")
    if pair in BRANCH_LIUHAI:
        return (6, f"{label}{z1}与{z2}六害，注意沟通方式避免误会。", f"{z1}与{z2}六害")
    return (8, f"{label}{z1}与{z2}无特殊冲合，相处平和。", f"{z1}与{z2}无特殊关系")


def _analyze_element_pair(el1: str, el2: str, dm1: str, dm2: str) -> tuple:
    if el1 == el2:
        return (15, f"双方日主同为{el1}，性格相近志趣相投，但也容易坚持己见。")
    if GENERATING.get(el1) == el2:
        return (22, f"{dm1}({el1})生{dm2}({el2})，前者愿意为后者付出。")
    if GENERATING.get(el2) == el1:
        return (22, f"{dm2}({el2})生{dm1}({el1})，后者愿意为前者付出。")
    if CONTROLLING.get(el1) == el2:
        return (12, f"{dm1}({el1})克{dm2}({el2})，前者在关系中较强势。")
    if CONTROLLING.get(el2) == el1:
        return (12, f"{dm2}({el2})克{dm1}({el1})，后者在关系中较强势。")
    return (10, "五行关系较复杂，需具体分析。")


def _analyze_heavenly_stems(p1: dict, p2: dict) -> tuple:
    """天干五合分析（年/月/日/时干）。"""
    keys = ["year", "month", "day", "hour"]
    match_count = 0
    details = []
    for k in keys:
        g1 = p1.get(k, {}).get("gan", "")
        g2 = p2.get(k, {}).get("gan", "")
        if g1 and g2 and HEAVENLY_HE.get(g1) == g2:
            elem = HEAVENLY_HE_ELEMENT.get((g1, g2), "")
            match_count += 1
            details.append(f"{'年日月时'[keys.index(k)]}干{g1}{g2}五合（{elem}）")
    if match_count >= 2:
        return (10, f"天干有{match_count}处五合：{'；'.join(details)}。上层沟通和默契度较好。")
    elif match_count == 1:
        return (6, f"天干有1处五合：{details[0]}。有一定的沟通共鸣基础。")
    else:
        return (3, "天干无明显五合，沟通方式需更多后天磨合。")


def _analyze_nayin(p1: dict, p2: dict) -> tuple:
    """纳音配对：年柱纳音五行生克。"""
    y1 = p1.get("year", {}).get("pillar", "")
    y2 = p2.get("year", {}).get("pillar", "")
    if not y1 or not y2:
        return (4, "纳音数据不足。")
    e1, e2 = NAYIN_ELEMENT.get(y1, ""), NAYIN_ELEMENT.get(y2, "")
    if not e1 or not e2:
        return (4, "纳音数据不足。")
    if e1 == e2:
        return (8, f"双方年柱纳音同为{e1}，气场相合。")
    if GENERATING.get(e1) == e2:
        return (8, f"甲方纳音{e1}生乙方纳音{e2}，气场顺遂。")
    if GENERATING.get(e2) == e1:
        return (8, f"乙方纳音{e2}生甲方纳音{e1}，气场顺遂。")
    if CONTROLLING.get(e1) == e2:
        return (4, f"甲方纳音{e1}克乙方纳音{e2}，气场有冲突。")
    if CONTROLLING.get(e2) == e1:
        return (4, f"乙方纳音{e2}克甲方纳音{e1}，气场有冲突。")
    return (5, f"纳音{e1}与{e2}，关系一般。")


def _analyze_favorable_complement(fav1: set, fav2: set, fe1: set, fe2: set) -> tuple:
    """喜用神互补：一方的喜用是否为对方旺五行。"""
    score = 4
    details = []
    cross1 = fav1 & fe2  # 1's favorable in 2's elements
    cross2 = fav2 & fe1
    if cross1:
        score += 3
        details.append(f"甲方喜用{'、'.join(cross1)}在乙方五行中出现")
    if cross2:
        score += 3
        details.append(f"乙方喜用{'、'.join(cross2)}在甲方五行中出现")
    if details:
        return (min(10, score), "；".join(details))
    return (score, "双方喜用五行互补一般。")


def _analyze_element_complement_v2(fe1: dict, fe2: dict) -> tuple:
    """五行互补 V2：按具体强弱互补评分。"""
    if not fe1 or not fe2:
        return (10, "五行数据不全")
    el_all = ["木","火","土","金","水"]
    score = 10
    for e in el_all:
        v1 = float(fe1.get(e, 0))
        v2 = float(fe2.get(e, 0))
        if v1 == 0 and v2 > 0:
            score += 2
        elif v2 == 0 and v1 > 0:
            score += 2
    return (min(20, score), "五行互补检查完成。")


def _analyze_ten_god_compatibility(tg1: dict, tg2: dict, dm1: str, dm2: str) -> int:
    score = 5
    c1 = tg1.get("正财",0)+tg1.get("偏财",0)
    c2 = tg2.get("正财",0)+tg2.get("偏财",0)
    if c1 > 0 and c2 > 0: score += 2
    y1 = tg1.get("正印",0)+tg1.get("偏印",0)
    y2 = tg2.get("正印",0)+tg2.get("偏印",0)
    s1 = tg1.get("食神",0)+tg1.get("伤官",0)
    s2 = tg2.get("食神",0)+tg2.get("伤官",0)
    if (y1 > 2 and s2 > 2) or (y2 > 2 and s1 > 2): score += 3
    return min(10, score)


def _analyze_daxian_sync(ld1: dict | None, ld2: dict | None, c1: dict, c2: dict) -> tuple:
    """大运同步性：比较当前大运阶段的协调性。"""
    score = 3
    detail = "大运数据不足，按基准分评估。"
    try:
        from core.luck_engine import get_luck_cycles
        if ld1 and ld2:
            dy1 = ld1.get("dayun_list", [])
            dy2 = ld2.get("dayun_list", [])
            if dy1 and dy2:
                current1 = next((d for d in dy1), {})
                current2 = next((d for d in dy2), {})
                if current1 and current2:
                    lv1 = current1.get("stage_level", "")
                    lv2 = current2.get("stage_level", "")
                    favorable = ["佳运","吉运","上升期"]
                    if lv1 in favorable and lv2 in favorable:
                        return (6, "双方当前均处较有利的大运阶段，同步性良好。")
                    elif lv1 not in favorable and lv2 not in favorable:
                        return (4, "双方当前大运都面临一定挑战，可互相扶持。")
                    else:
                        return (5, "双方大运阶段节奏不同，需要更多磨合和理解。")
    except Exception:
        pass
    return (score, detail)


# ====== 命主特质 + 合/不合分析 + 建议（v1.3-A 扩展）======

DM_PERSONALITY = {
    "甲": {"type": "大树型", "style": "主动进取型",
              "desc": "上进、有领导力、目标感强，态度正直不喜弯绕。",
              "pair": "希望伴侣理解自己的大局观，而非环节上的纠结。"},
    "乙": {"type": "花草型", "style": "温和适应型",
              "desc": "温柔灵活、适应力强、细腻周到，不喜硬碰硬的沟通方式。",
              "pair": "需要安全感和细节上的关怀，过于粗籗的方式会让其不安。"},
    "丙": {"type": "太阳型", "style": "热情主动型",
              "desc": "热情外向、有感染力、行动力强，喜欢直来直往的沟通。",
              "pair": "希望得到兴奋和鼓励，而非浇冷水或负面评价。"},
    "丁": {"type": "烛火型", "style": "内收专注型",
              "desc": "细腻执着、洞察力强、内心热烈，表面平静但情感丰富。",
              "pair": "需要被理解和被认真对待，轻率的态度会让其失望。"},
    "戊": {"type": "泰山型", "style": "稳重务实型",
              "desc": "厚重稳重、有包容力、务实可靠，但有时过于固执。",
              "pair": "需要尊重和稳定的关系节奏，过于变幻莫测的方式会让其焦虑。"},
    "己": {"type": "田园型", "style": "服务支持型",
              "desc": "内收务实、服务心强、耐心细致，喜欢默默付出。",
              "pair": "需要被看见和被感谢，付出被忽略是最大的伤害。"},
    "庚": {"type": "钢铁型", "style": "果敢执行型",
              "desc": "刚强果断、有原则、执行力强，偏向事实和逻辑。",
              "pair": "需要直接的沟通，隐忍和掣摩会让其焦躁。"},
    "辛": {"type": "珠宝型", "style": "精益求精型",
              "desc": "精致理性、有审美、注重品质，对细节和品质要求较高。",
              "pair": "需要品质和深度的交流，粗糙或平庸的方式难以吸引其。"},
    "壬": {"type": "江河型", "style": "智慧开放型",
              "desc": "大气智慧、有谋略、开放包容，喜欢大局面的思考。",
              "pair": "希望伴侣能理解自己的梦想，而非只关注现实问题。"},
    "癸": {"type": "雨露型", "style": "灵动观察型",
              "desc": "细腻敏感、有灵性、善于观察，情感丰富且容易受环境影响。",
              "pair": "需要情感上的共鸣和安全感，理性过强会让其感到孤独。"},
}


def _describe_person(chart: dict) -> dict:
    """分析命主特质描述。"""
    dm = chart.get("day_master", "")
    info = DM_PERSONALITY.get(dm, {"type": "", "style": "", "desc": "", "pair": ""})
    strength = chart.get("day_master_strength", {})
    strength_text = strength.get("strength", "中等")
    fe = chart.get("five_elements", {})
    fe_sorted = sorted(fe.items(), key=lambda x: -float(x[1])) if fe else []
    strongest = fe_sorted[0][0] if fe_sorted else ""
    weakest = fe_sorted[-1][0] if len(fe_sorted) > 1 else ""
    favorable = strength.get("favorable_elements", []) or []
    profile = chart.get("profile", {})
    name = profile.get("name", "未命名")
    name2 = name.split("(")[0] if "(" in name else name

    return {
        "name": name2,
        "day_master": dm,
        "type": info["type"],
        "style": info["style"],
        "description": f"日主{info['type']}，{info['desc']}命局{strength_text}",
        "core_traits": [f"日主<{dm}>{info['type']}，{info['style']}",
                        f"命局{strength_text}，喜用{'、'.join(favorable) if favorable else '待定'}",
                        f"最强五行<{strongest}>" if strongest else "",
                        f"最弱五行<{weakest}>" if weakest else ""],
        "pair_expectation": info["pair"],
    }


def _generate_match_reasons(dimensions: list, chart1: dict, chart2: dict) -> list[str]:
    """分析为什么合——提取高分维度。"""
    reasons = []
    for d in dimensions:
        pct = d["score"] / d["max_score"] if d["max_score"] > 0 else 0
        if pct >= 0.7:
            label = d["label"]
            detail = d.get("detail", "")
            if "六合" in d.get("text", ""):
                reasons.append(f"{label}：六合关系，相处自然默契。")
            elif "生" in d.get("text", "") and "日主" in label:
                reasons.append(f"{label}：一方愿为另一方付出，关系基础良好。")
            elif "五行互补" in label and pct >= 0.8:
                reasons.append(f"五行互补性良好，能在生活和性格上互补。")
            elif "喜用神互补" in label and pct >= 0.6:
                reasons.append(f"喜用神互补，对方的优势能够补充自己的短板。")
            elif "天干五合" in label:
                reasons.append(f"天干五合，沟通默契度较高，容易理解对方的意图。")
            elif "纳音" in label and pct >= 0.7:
                reasons.append(f"纳音配对相生，气场和谐。")
    if not reasons:
        reasons.append("基础维度评分中规中矩，没有明显冲突，后天磨合空间较大。")
    return reasons[:4]


def _generate_conflict_reasons(dimensions: list, chart1: dict, chart2: dict) -> list[str]:
    """分析为什么不合——提取低分维度。"""
    reasons = []
    for d in dimensions:
        pct = d["score"] / d["max_score"] if d["max_score"] > 0 else 0
        if pct < 0.4:
            label = d["label"]
            text = d.get("text", "")
            if "六冲" in text:
                reasons.append(f"{label}冲突，这是需要重点关注的磨合点。")
            elif "克" in text and "日主" in label:
                reasons.append(f"{label}，方一方较强势，需注意权力平衡。")
            elif "六害" in text:
                reasons.append(f"{label}，沟通方式上容易产生误会，需更多耐心。")
    if not reasons:
        reasons.append("各维度未发现明显冲突，关系基础较为平稳。")
    return reasons[:3]


def _generate_compatibility_advice(dimensions: list, chart1: dict, chart2: dict) -> list[str]:
    """根据合/不合分析给出具体建议。"""
    advice = []
    has_liuchong = any("六冲" in d.get("text", "") for d in dimensions)
    has_ke = any("克" in d.get("text", "") and "日主" in d.get("label", "") for d in dimensions)
    has_liuhai = any("六害" in d.get("text", "") for d in dimensions)
    has_weak_fav = any("喜用神互补" in d.get("label", "") and d["score"] / d["max_score"] < 0.4 for d in dimensions)
    has_weak_element = any("五行互补" in d.get("label", "") and d["score"] / d["max_score"] < 0.4 for d in dimensions)

    if has_liuchong:
        advice.append("地支冲突提示：重要事务建议多沟通、少用情绪做决定，当发现分歧时，先确认对方的真实意图再回应。")
    if has_ke:
        advice.append("日主克制提示：强势的一方需要留意对方的尊严，重要决策上建议多征求意见、免得让对方感觉被忽视。")
    if has_liuhai:
        advice.append("六害提示：日常沟通中多确认对方的真实想法，避免“我以为你知道”的思维模式。")
    if has_weak_fav or has_weak_element:
        advice.append("互补性不足提示：可以通过共同培养某些兴趣或生活习惯来增强互动质量，而非追求对方成为自己的样子。")
    if not advice:
        advice.append("各维度评分较为均衡，建议保持当前的沟通节奏，在关键事务上继续保持互相尊重和支持。")

    return advice[:4]
