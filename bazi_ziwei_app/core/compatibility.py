"""八字合婚/合盘匹配分析。

基于双方八字的手工排盘数据，从地支关系、日主五行、十神互参等维度做综合判断。
"""

from __future__ import annotations

from core.bazi_constants import STEM_ELEMENTS, GENERATING, CONTROLLING
from core.ten_gods import get_ten_god


# 地支六合
BRANCH_LIUHE = frozenset({
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
})

# 地支三合
BRANCH_SANHE = frozenset({
    frozenset(("申", "子", "辰")),
    frozenset(("亥", "卯", "未")),
    frozenset(("寅", "午", "戌")),
    frozenset(("巳", "酉", "丑")),
})

# 地支六冲
BRANCH_LIUCHONG = frozenset({
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
})

# 地支六害
BRANCH_LIUHAI = frozenset({
    frozenset(("子", "未")),
    frozenset(("丑", "午")),
    frozenset(("寅", "巳")),
    frozenset(("卯", "辰")),
    frozenset(("申", "亥")),
    frozenset(("酉", "戌")),
})


def analyze_compatibility(chart1: dict, chart2: dict) -> dict:
    """分析两个命盘的合婚匹配程度。"""
    results = {
        "overall_score": 0,
        "dimensions": [],
        "summary": "",
    }

    # 1. 年支关系 (15分)
    year_zhi1 = chart1.get("pillars", {}).get("year", {}).get("zhi", "")
    year_zhi2 = chart2.get("pillars", {}).get("year", {}).get("zhi", "")
    if year_zhi1 and year_zhi2:
        yr_score, yr_text, yr_label = _analyze_branch_pair(year_zhi1, year_zhi2, "年支")
        results["dimensions"].append({
            "label": "年支关系",
            "score": yr_score,
            "max_score": 15,
            "text": yr_text,
            "detail": yr_label,
        })

    # 2. 月支关系 (10分)
    month_zhi1 = chart1.get("pillars", {}).get("month", {}).get("zhi", "")
    month_zhi2 = chart2.get("pillars", {}).get("month", {}).get("zhi", "")
    if month_zhi1 and month_zhi2:
        mr_score, mr_text, mr_label = _analyze_branch_pair(month_zhi1, month_zhi2, "月支")
        results["dimensions"].append({
            "label": "月支关系",
            "score": mr_score,
            "max_score": 10,
            "text": mr_text,
            "detail": mr_label,
        })

    # 3. 日支关系 (20分，最重要的配对指标)
    day_zhi1 = chart1.get("pillars", {}).get("day", {}).get("zhi", "")
    day_zhi2 = chart2.get("pillars", {}).get("day", {}).get("zhi", "")
    if day_zhi1 and day_zhi2:
        dr_score, dr_text, dr_label = _analyze_branch_pair(day_zhi1, day_zhi2, "日支（夫妻宫）")
        results["dimensions"].append({
            "label": "日支关系",
            "score": dr_score,
            "max_score": 20,
            "text": dr_text,
            "detail": dr_label,
        })

    # 4. 日主五行关系 (25分)
    dm1 = chart1.get("day_master", "")
    dm2 = chart2.get("day_master", "")
    if dm1 and dm2:
        el1 = STEM_ELEMENTS.get(dm1, "")
        el2 = STEM_ELEMENTS.get(dm2, "")
        if el1 and el2:
            dm_score, dm_text = _analyze_element_pair(el1, el2, dm1, dm2)
            results["dimensions"].append({
                "label": "日主五行",
                "score": dm_score,
                "max_score": 25,
                "text": dm_text,
                "detail": f"甲方日主: {dm1}({el1})，乙方日主: {dm2}({el2})",
            })

    # 5. 五行互补 (20分)
    fe1 = set(chart1.get("five_elements", {}).keys())
    fe2 = set(chart2.get("five_elements", {}).keys())
    complement_score = _analyze_element_complement(fe1, fe2)
    results["dimensions"].append({
        "label": "五行互补",
        "score": complement_score,
        "max_score": 20,
        "text": f"命主五行: {'、'.join(sorted(fe1))}，对方五行: {'、'.join(sorted(fe2))}" if fe1 and fe2 else "",
        "detail": f"双方五行{'互补性较好' if complement_score >= 12 else '有一定的互补性' if complement_score >= 8 else '互补性一般'}" if fe1 and fe2 else "五行数据不全",
    })

    # 6. 十神互参 (10分)
    tg_count1 = chart1.get("ten_god_counts", {})
    tg_count2 = chart2.get("ten_god_counts", {})
    tg_score = _analyze_ten_god_compatibility(tg_count1, tg_count2, dm1, dm2)
    results["dimensions"].append({
        "label": "十神互参",
        "score": tg_score,
        "max_score": 10,
        "text": f"财星互补: {'互补有利' if tg_count1.get('正财',0)+tg_count1.get('偏财',0) > 0 and tg_count2.get('正财',0)+tg_count2.get('偏财',0) > 0 else '一方偏重'}",
        "detail": "",
    })

    # 总分
    total_score = sum(d["score"] for d in results["dimensions"])
    results["overall_score"] = total_score

    # 综合评语
    if total_score >= 70:
        results["summary"] = "双方八字匹配度较高，命理层面有较好的互补性和协调性。"
        results["level"] = "上佳"
    elif total_score >= 55:
        results["summary"] = "双方八字有一定匹配度，部分维度存在互补，部分维度需要磨合。"
        results["level"] = "良好"
    elif total_score >= 40:
        results["summary"] = "双方八字匹配度一般，在关键维度上需要注意协调和理解。"
        results["level"] = "中等"
    else:
        results["summary"] = "双方八字匹配度较低，在重要维度上存在较大差异，需要更多的包容和努力。"
        results["level"] = "较低"

    return results


def _analyze_branch_pair(zhi1: str, zhi2: str, label: str) -> tuple:
    """分析两个地支的关系。"""
    pair = frozenset((zhi1, zhi2))
    
    if pair in BRANCH_LIUHE:
        return (15 if "年支" in label or "日支" in label else 10,
                f"{label}形成六合，是良配信号。",
                f"{zhi1}与{zhi2}六合")
    
    # Check if both are in any SanHe set
    for sanhe_set in BRANCH_SANHE:
        if zhi1 in sanhe_set and zhi2 in sanhe_set:
            return (12 if "日支" in label else 8,
                    f"{label}形成三合，相处融洽。",
                    f"{zhi1}与{zhi2}三合")
    
    if pair in BRANCH_LIUCHONG:
        return (5 if "日支" in label else 3,
                f"{label}形成六冲，需要多加磨合。",
                f"{zhi1}与{zhi2}六冲")
    
    if pair in BRANCH_LIUHAI:
        return (6 if "日支" in label else 4,
                f"{label}形成六害，需要注意沟通方式。",
                f"{zhi1}与{zhi2}六害")
    
    # 无特殊关系
    return (8, f"{label}无特殊冲合关系，相处平和。",
            f"{zhi1}与{zhi2}无特殊关系")


def _analyze_element_pair(el1: str, el2: str, dm1: str, dm2: str) -> tuple:
    """分析日主五行生克关系。"""
    if el1 == el2:
        return (15, f"双方日主同为{el1}，五行相同，志趣相投但也容易固执己见。")
    
    if GENERATING.get(el1) == el2:  # el1生el2
        return (22, f"甲方日主{dm1}({el1})生乙方日主{dm2}({el2})，甲方愿意为乙方付出。")
    
    if GENERATING.get(el2) == el1:  # el2生el1
        return (22, f"乙方日主{dm2}({el2})生甲方日主{dm1}({el1})，乙方愿意为甲方付出。")
    
    if CONTROLLING.get(el1) == el2:  # el1克el2
        return (12, f"甲方日主{dm1}({el1})克乙方日主{dm2}({el2})，甲方在关系中较为强势。")
    
    if CONTROLLING.get(el2) == el1:  # el2克el1
        return (12, f"乙方日主{dm2}({el2})克甲方日主{dm1}({el1})，乙方在关系中较为强势。")
    
    return (10, "五行关系较为复杂，需要具体分析。")

def _analyze_element_complement(fe1: set, fe2: set) -> int:
    """分析五行互补性。"""
    if not fe1 or not fe2:
        return 10
    
    missing1 = set(STEM_ELEMENTS.values()) - fe1
    missing2 = set(STEM_ELEMENTS.values()) - fe2
    
    score = 10
    # 对方有自己缺失的五行 = 加分
    for e in missing1:
        if e in fe2:
            score += 3
    for e in missing2:
        if e in fe1:
            score += 3
    
    return min(20, score)


def _analyze_ten_god_compatibility(tg1: dict, tg2: dict, dm1: str, dm2: str) -> int:
    """分析十神互补性。"""
    score = 5
    # 如果双方都有财星，说明价值观都重视物质
    if tg1.get("正财", 0) + tg1.get("偏财", 0) > 0 and tg2.get("正财", 0) + tg2.get("偏财", 0) > 0:
        score += 2
    # 如果一方印旺一方食伤旺，形成互补
    if (tg1.get("正印", 0) + tg1.get("偏印", 0) > 2) and (tg2.get("食神", 0) + tg2.get("伤官", 0) > 2):
        score += 3
    if (tg2.get("正印", 0) + tg2.get("偏印", 0) > 2) and (tg1.get("食神", 0) + tg1.get("伤官", 0) > 2):
        score += 3
    return min(10, score)
