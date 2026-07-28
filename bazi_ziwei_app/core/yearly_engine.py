"""年度运程分析。"""

from __future__ import annotations

import core.four_pillars_engine as four_pillars_engine
from core.bazi_constants import BRANCH_HIDDEN_STEMS, BRANCH_MAIN_ELEMENTS, EARTHLY_BRANCHES, HEAVENLY_STEMS, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.report_diversity import build_chart_signature_text
from core.ten_gods import get_ten_god
from report.narrative_engine import build_yearly_narrative


TEN_GOD_THEMES: dict[str, dict[str, str | list[str]]] = {
    "比肩": {
        "keywords": ["自我", "竞争", "同辈"],
        "theme": "比肩之年自我意识和独立行动会更明显，适合稳住节奏，也要留意同业竞争和合作边界。",
    },
    "劫财": {
        "keywords": ["合作", "朋友", "边界"],
        "theme": "劫财之年人际互动和资源往来较活跃，适合借力合作，也要提前说清分工与成本。",
    },
    "食神": {
        "keywords": ["表达", "技能", "作品"],
        "theme": "食神之年适合输出专业能力、内容作品和稳定成果，整体宜用长期主义推进。",
    },
    "伤官": {
        "keywords": ["创意", "突破", "表达"],
        "theme": "伤官之年表达欲和突破意识较明显，适合创新与展示，也需要注意规则和沟通方式。",
    },
    "正财": {
        "keywords": ["收入", "预算", "资源"],
        "theme": "正财之年更适合关注稳定收入、预算管理和现实资源的积累。",
    },
    "偏财": {
        "keywords": ["项目", "机会", "商业"],
        "theme": "偏财之年容易关注项目机会和资源整合，适合谨慎评估收益与投入。",
    },
    "正官": {
        "keywords": ["规则", "责任", "职位"],
        "theme": "正官之年责任感、规则意识和职位目标会更突出，适合建立秩序与长期信用。",
    },
    "七杀": {
        "keywords": ["压力", "管理", "挑战"],
        "theme": "七杀之年目标压力和外部挑战较明显，适合提升执行力，也要重视身心节奏。",
    },
    "正印": {
        "keywords": ["学习", "贵人", "系统"],
        "theme": "正印之年适合学习进修、获取支持、建立方法体系，并给自己更多恢复空间。",
    },
    "偏印": {
        "keywords": ["研究", "灵感", "调整"],
        "theme": "偏印之年适合研究、复盘、专业深化和思维升级，但要避免想得多做得少。",
    },
    "未知": {
        "keywords": ["观察", "积累", "调整"],
        "theme": "本年十神信息暂不完整，建议以稳步观察和现实反馈为主。",
    },
}


def _cycle_pillar(index: int) -> str:
    """按六十甲子循环生成干支。"""
    stem = HEAVENLY_STEMS[index % len(HEAVENLY_STEMS)]
    branch = EARTHLY_BRANCHES[index % len(EARTHLY_BRANCHES)]
    return f"{stem}{branch}"


def _fallback_year_pillar(year: int) -> str:
    """缺少日历库时按 1984 甲子年简化推算流年干支。"""
    return _cycle_pillar((year - 1984) % 60)


def get_year_pillar(target_year: int) -> str:
    """通过项目四柱引擎的唯一干支循环入口取得流年干支。"""
    return four_pillars_engine.year_pillar_for_effective_year(int(target_year))


def _split_pillar(pillar: str) -> tuple[str, str]:
    """拆分干支。"""
    return (pillar[0], pillar[1]) if len(pillar) >= 2 else ("", "")


def _relation_score(elements: list[str], favorable: set[str], unfavorable: set[str]) -> tuple[int, str]:
    """判断年度五行与喜忌的关系。"""
    score = 0
    has_favorable = False
    has_unfavorable = False
    for element in elements:
        if element in favorable:
            score += 2
            has_favorable = True
        if element in unfavorable:
            score -= 2
            has_unfavorable = True
    if score >= 2:
        return score, "喜用相关"
    if score <= -2:
        return score, "忌神相关"
    if has_favorable and has_unfavorable:
        return score, "喜忌混杂"
    return score, "平稳观察"


def _level(score: int) -> str:
    """把关系分转为年度层级。"""
    if score >= 3:
        return "助力较明显"
    if score >= 1:
        return "小有助力"
    if score <= -3:
        return "压力较明显"
    if score <= -1:
        return "略有压力"
    return "平稳观察"


def _theme(ten_god: str) -> dict[str, str | list[str]]:
    """返回十神主题。"""
    return TEN_GOD_THEMES.get(ten_god, TEN_GOD_THEMES["未知"])


def _branch_ten_god(chart: dict, branch: str) -> str:
    """用地支主气推导十神。"""
    hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
    if hidden:
        return get_ten_god(chart.get("day_master", ""), hidden[0])
    return "未知"


def _current_luck_note(luck_data: dict | None, target_year: int) -> str:
    """提取当前年份所在大运背景。"""
    if not luck_data or not luck_data.get("available"):
        return ""
    for item in luck_data.get("dayun_list", []):
        try:
            start_year = int(item.get("start_year", 0))
            end_year = int(item.get("end_year", 0))
        except (TypeError, ValueError):
            continue
        if start_year <= target_year <= end_year:
            start_date = str(item.get("start_date", ""))
            boundary_note = ""
            try:
                from datetime import date

                boundary = date.fromisoformat(start_date)
                if boundary.year == target_year and (boundary.month, boundary.day) != (1, 1):
                    boundary_note = f" 该年于{boundary.month}月{boundary.day}日换入此运，年初仍属上一运。"
            except ValueError:
                pass
            return (
                f" 当前大运背景为{item.get('pillar', '')}，可把本年变化放在"
                f"{item.get('start_year', '')}-{item.get('end_year', '')}年的十年阶段中观察。"
                f"{boundary_note}"
            )
    return " 当前未匹配到具体大运区间，可先按流年本身和原局关系观察。"


def _month_attention(chart: dict, target_year: int) -> tuple[list[str], list[str]]:
    """根据流月喜忌和风险，提取高关注月份与机会月份。"""
    try:
        from core.monthly_engine import analyze_monthly_fortune

        monthly_data = analyze_monthly_fortune(chart, target_year)
    except Exception:
        return [], []
    high_attention = []
    opportunity = []
    mixed_candidates = []
    steady_candidates = []
    for item in monthly_data:
        label = f"{item.get('month_name', '')}（{item.get('pillar', '')}）"
        if item.get("relation_to_favorable") == "忌神相关" or item.get("branch_relations"):
            high_attention.append(label)
        if item.get("relation_to_favorable") == "喜用相关":
            opportunity.append(label)
        elif item.get("relation_to_favorable") == "喜忌混杂":
            mixed_candidates.append(label)
        elif item.get("relation_to_favorable") == "平稳观察" and not item.get("branch_relations"):
            steady_candidates.append(label)
    return high_attention[:4], opportunity[:4]


def _career_text(ten_god: str, relation: str) -> str:
    """生成事业文案。"""
    base = _theme(ten_god)["theme"]
    if relation == "喜用相关":
        return f"事业方面，{base} 若现实条件成熟，适合主动推进计划、争取资源和沉淀成果。"
    if relation == "忌神相关":
        return f"事业方面，{base} 建议控制节奏，少做高成本试错，重要选择多做复盘。"
    return f"事业方面，{base} 适合稳步推进，不宜只凭单一年份判断方向好坏。"


def _wealth_text(ten_god: str, relation: str) -> str:
    """生成财富文案。"""
    if ten_god in {"正财", "偏财"}:
        focus = "财富议题会更容易被看见，适合重视预算、现金流、项目回报和资源配置。"
    elif ten_god in {"食神", "伤官"}:
        focus = "适合通过技能、内容、服务和项目输出逐步创造收益。"
    elif ten_god in {"比肩", "劫财"}:
        focus = "朋友、同业或合作相关的资源往来会更明显，合伙与借贷边界需要更清楚。"
    else:
        focus = "财富方面建议保持稳健，优先提升能力、信用和抗波动能力。"
    if relation == "忌神相关":
        return f"{focus} 本年对消耗和风险边界需要更敏感。"
    return focus


def _relationship_text(ten_god: str) -> str:
    """生成关系文案。"""
    if ten_god in {"比肩", "劫财"}:
        return "关系方面，同辈、朋友、合作伙伴互动较多，建议提前沟通期待和边界。"
    if ten_god in {"正官", "七杀"}:
        return "关系方面，责任、承诺和压力议题可能更突出，适合用稳定沟通降低误解。"
    if ten_god in {"食神", "伤官"}:
        return "关系方面，表达和情绪反馈较明显，建议把真实想法说清楚，也给对方留空间。"
    return "关系方面，适合保持温和沟通，重要决定多结合现实相处体验判断。"


def _health_text(relation: str) -> str:
    """生成身心节奏文案。"""
    if relation == "忌神相关":
        return "身心节奏方面，需要注意压力累积、作息紊乱和过度消耗，建议把休息与运动纳入计划。"
    if relation == "喜用相关":
        return "身心节奏方面，整体更适合建立稳定习惯，通过规律作息和持续学习增强承接力。"
    return "身心节奏方面，以稳定作息、适度运动和情绪管理为主，避免长期透支。"




# ===== 月度分类与增强专项分析 =====

# 桃花年份映射（年支 → 桃花支）
LOTUS_BRANCHES = {
    "申": "酉", "子": "酉", "辰": "酉",
    "亥": "子", "卯": "子", "未": "子",
    "寅": "卯", "午": "卯", "戌": "卯",
    "巳": "午", "酉": "午", "丑": "午",
}

# 五行对应身体健康
ELEMENT_HEALTH = {
    "木": "肝胆、筋骨、神经系统",
    "火": "心脏、血液循环、眼部",
    "土": "脾胃、消化系统、皮肤",
    "金": "肺部、呼吸道、大肠",
    "水": "肾脏、泌尿系统、内分泌",
}

# 事业关键十神
CAREER_GODS = {"正官", "七杀", "正印", "偏印"}
# 财富关键十神
WEALTH_GODS = {"正财", "偏财", "食神", "伤官"}
# 关系关键十神（男命以财为妻，女命以官杀为夫）
RELATION_GODS_MALE = {"正财", "偏财"}
RELATION_GODS_FEMALE = {"正官", "七杀"}


def _get_taohua_month(year_zhi: str, monthly_data: list) -> list[str]:
    """检测流月中哪些月份是桃花月。"""
    target = LOTUS_BRANCHES.get(year_zhi, "")
    if not target:
        return []
    peach = []
    for m in monthly_data:
        if m.get("zhi", "") == target:
            peach.append(m.get("month_name", ""))
    return peach


def _classify_months_for(monthly_data: list, target_gods: set) -> tuple[list[str], list[str]]:
    """根据指定十神分类，从月度数据中提取利好月份和谨慎月份。"""
    good, bad = [], []
    for m in monthly_data:
        name = m.get("month_name", "")
        tg = m.get("ten_god", "")
        rel = m.get("relation_to_favorable", "")
        if tg in target_gods:
            if rel == "喜用相关":
                good.append(name)
            elif rel == "忌神相关":
                bad.append(name)
    return good[:4], bad[:4]


def _get_health_concerns(chart: dict, target_year: int, monthly_data: list) -> list[str]:
    """分析年度健康隐患。"""
    strength = chart.get("day_master_strength", {})
    unfavorable = set(strength.get("unfavorable_elements", []))
    concerns = []
    for m in monthly_data:
        if m.get("relation_to_favorable") == "忌神相关":
            zhi_el = m.get("zhi_element", "")
            if zhi_el in unfavorable and zhi_el in ELEMENT_HEALTH:
                concern = f"{m.get('month_name', '')}前后注意{ELEMENT_HEALTH[zhi_el]}"
                if concern not in concerns:
                    concerns.append(concern)
    # Also check overall yearly relation
    return concerns[:4]


def _get_taohua_text(peach_months: list[str]) -> str:
    """生成桃花分析文案。"""
    if not peach_months:
        return "本年度未出现明显的桃花月份，感情方面以顺其自然为主。"
    months_str = "、".join(peach_months)
    if len(peach_months) >= 2:
        return f"{months_str}前后桃花能量较明显，社交场合容易遇到有缘人，主动参与社交活动会有更多机会。"
    return f"{months_str}前后桃花能量较突出，可以多留意身边的社交机会。"


def _gender_from_profile(profile: dict) -> str:
    return profile.get("gender", "男")


def _enhance_career_text(base_text: str, good_months: list[str], bad_months: list[str]) -> str:
    """在基础事业文本基础上，加入月度分析。"""
    parts = [base_text]
    if good_months:
        parts.append(f"📈 {', '.join(good_months)}前后事业能量较顺畅，适合推进重要项目或争取机会。")
    if bad_months:
        parts.append(f"⚠️ {', '.join(bad_months)}前后容易遇到阻碍或压力，建议放慢节奏、多做准备。")
    return " ".join(parts)


def _get_wealth_level(ten_god: str, relation: str, overall_level: str) -> str:
    """根据十神和关系评定年度财运等级。"""
    if relation == "喜用相关":
        if ten_god in {"正财", "偏财"}:
            return "🟢 上等财运：今年财星得力，正财偏财均有不错机会，适合积极理财和投资布局。"
        if ten_god in {"食神", "伤官"}:
            return "🟢 中上财运：才华变现能力增强，适合通过技能、创作和服务创造收益。"
        return "🟡 中等偏上财运：整体财务环境有利，适度进取能有所收获。"
    elif relation == "平稳观察":
        return "🟡 中等财运：财务环境平稳，适合稳健理财，不宜冒进。"
    elif relation == "喜忌混杂":
        return "🟠 波动财运：财运有起有落，把握机会的同时也要控制风险。"
    elif relation == "忌神相关":
        if ten_god in {"正财", "偏财"}:
            return "🔴 压力财运：财星受制，需注意财务压力和意外支出，保守为上。"
        return "🔴 谨慎财运：财务方面容易有消耗，建议控制开支、减少高风险投资。"
    return "🟡 财运平稳，按部就班即可。"


def _enhance_wealth_text(base_text: str, good_months: list[str], bad_months: list[str], ten_god: str = "", relation: str = "", overall_level: str = "") -> str:
    """在基础财富文本基础上，加入月度分析和财运等级。"""
    parts = []
    # 财运等级
    level_text = _get_wealth_level(ten_god, relation, overall_level)
    parts.append(level_text)
    parts.append("")
    parts.append(base_text)
    if good_months:
        parts.append(f"💰 {', '.join(good_months)}前后财运机会较好，适合主动争取和把握。")
    if bad_months:
        parts.append(f"⚠️ {', '.join(bad_months)}前后财务波动较大，注意控制开支和风险。")
    return " ".join(parts)


def _enhance_relationship_text(base_text: str, good_months: list[str], bad_months: list[str], peach_months: list[str], gender: str) -> str:
    """在基础关系文本基础上，加入月度分析和桃花。"""
    parts = [base_text]
    if peach_months:
        parts.append(f"🌸 {', '.join(peach_months)}前后感情桃花机会较明显。")
    elif gender == "男":
        if good_months:
            parts.append(f"💞 {', '.join(good_months)}前后感情运较好，适合增进关系或主动表达。")
    elif gender == "女":
        if good_months:
            parts.append(f"💞 {', '.join(good_months)}前后感情运较好，适合增进关系或主动表达。")
    if bad_months:
        parts.append(f"⚠️ {', '.join(bad_months)}前后感情容易有摩擦，注意沟通方式。")
    return " ".join(parts)


def _enhance_health_text(base_text: str, health_concerns: list[str]) -> str:
    """在基础健康文本基础上，加入具体部位提醒。"""
    parts = [base_text]
    if health_concerns:
        parts.append(f"🏥 {'；'.join(health_concerns)}。")
    return " ".join(parts)


def analyze_yearly_fortune(
    chart: dict,
    target_year: int,
    luck_data: dict | None = None,
    *,
    include_monthly_analysis: bool = True,
) -> dict:
    """
    根据命盘和目标年份生成年度运程。
    """
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    pillar = get_year_pillar(target_year)
    gan, zhi = _split_pillar(pillar)
    gan_element = STEM_ELEMENTS.get(gan, "")
    zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
    ten_god = get_ten_god(day_master, gan) if gan else "未知"
    branch_ten_god = _branch_ten_god(chart, zhi)
    branch_relations = analyze_year_branch_relations(chart, zhi)
    score, relation = _relation_score([gan_element, zhi_element], favorable, unfavorable)
    overall_level = _level(score)
    theme = _theme(ten_god)
    keywords = list(theme["keywords"])
    if relation not in keywords:
        keywords.append(relation)
    for item in branch_relations:
        if item["label"] not in keywords:
            keywords.append(item["label"])

    narrative_seed = {
        "year": target_year,
        "pillar": pillar,
        "gan": gan,
        "zhi": zhi,
        "gan_element": gan_element,
        "zhi_element": zhi_element,
        "ten_god": ten_god,
        "branch_ten_god": branch_ten_god,
        "branch_relations": branch_relations,
    }
    narrative = build_yearly_narrative(chart, narrative_seed)
    luck_note = _current_luck_note(luck_data, target_year)
    high_attention_months = []
    opportunity_months = []
    enhanced_career = narrative["career_text"]
    enhanced_wealth = narrative["wealth_text"]
    enhanced_relationship = narrative["relationship_text"]
    enhanced_health = narrative["health_text"]
    peach_months = []
    career_good = career_bad = wealth_good = wealth_bad = rel_good = rel_bad = []
    health_concerns = []

    if include_monthly_analysis:
        high_attention_months, opportunity_months = _month_attention(chart, target_year)

        # 新增：月度分类分析
        try:
            from core.monthly_engine import analyze_monthly_fortune
            monthly_data = analyze_monthly_fortune(chart, target_year)
            prof = chart.get("profile", {})
            gender = _gender_from_profile(prof)
            year_zhi = get_year_pillar(target_year)[1] if len(get_year_pillar(target_year)) >= 2 else ""

            # 桃花分析
            peach_months = _get_taohua_month(year_zhi, monthly_data)

            # 各维度月份分类
            career_good, career_bad = _classify_months_for(monthly_data, CAREER_GODS)
            wealth_good, wealth_bad = _classify_months_for(monthly_data, WEALTH_GODS)
            rel_gods = RELATION_GODS_MALE if gender == "男" else RELATION_GODS_FEMALE
            rel_good, rel_bad = _classify_months_for(monthly_data, rel_gods)
            health_concerns = _get_health_concerns(chart, target_year, monthly_data)

            # 增强文本
            enhanced_career = _enhance_career_text(narrative["career_text"], career_good, career_bad)
            enhanced_wealth = _enhance_wealth_text(narrative["wealth_text"], wealth_good, wealth_bad, ten_god, relation, overall_level)
            enhanced_relationship = _enhance_relationship_text(narrative["relationship_text"], rel_good, rel_bad, peach_months, gender)
            enhanced_health = _enhance_health_text(narrative["health_text"], health_concerns)
        except Exception:
            pass

    signature = build_chart_signature_text(chart, "年度运程差异依据")
    overall_text = f"{narrative['overall_text']}{luck_note}\n{signature}"
    risk_text = narrative["risk_text"]
    advice_text = narrative["advice_text"]

    return {
        "year": target_year,
        "pillar": pillar,
        "gan": gan,
        "zhi": zhi,
        "gan_element": gan_element,
        "zhi_element": zhi_element,
        "ten_god": ten_god,
        "branch_ten_god": branch_ten_god,
        "branch_relations": branch_relations,
        "relation_to_favorable": relation,
        "overall_level": overall_level,
        "keywords": narrative.get("keywords", keywords),
        "annual_keywords": narrative.get("annual_keywords", narrative.get("keywords", keywords)),
        "overall_text": overall_text,
        "career_text": enhanced_career,
        "wealth_text": enhanced_wealth,
        "relationship_text": enhanced_relationship,
        "health_text": enhanced_health,
        "risk_text": risk_text,
        "advice_text": advice_text,
        "brief_text": f"{narrative['brief_text']} {target_year}年{signature.splitlines()[0]}",
        "suitable_actions": narrative["suitable_actions"],
        "actions_to_avoid": narrative["actions_to_avoid"],
        "high_attention_months": high_attention_months,
        "opportunity_months": opportunity_months,
        # 增强月度数据
        "career_good_months": career_good,
        "career_bad_months": career_bad,
        "wealth_good_months": wealth_good,
        "wealth_bad_months": wealth_bad,
        "peach_months": peach_months,
        "health_concerns": health_concerns,
    }
