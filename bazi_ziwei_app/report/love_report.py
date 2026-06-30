"""婚恋专项报告。"""

from __future__ import annotations

from core.chart_fingerprint import build_chart_fingerprint
from core.report_diversity import build_chart_signature_text
from report.export_report import DISCLAIMER
from report.special_report_common import _section


def _partner_star_label(profile: dict) -> str:
    """返回伴侣星标签。"""
    if profile.get("gender") == "女":
        return "官杀"
    if profile.get("gender") == "男":
        return "财星"
    return "伴侣星"


def _partner_star_count(fp: dict, profile: dict) -> int:
    """返回伴侣星数量。"""
    if profile.get("gender") == "女":
        return fp["officer_star_count"]
    if profile.get("gender") == "男":
        return fp["wealth_star_count"]
    return max(fp["wealth_star_count"], fp["officer_star_count"])


def _evidence(fp: dict, profile: dict) -> list[str]:
    """生成婚恋命盘依据。"""
    star_label = _partner_star_label(profile)
    star_count = _partner_star_count(fp, profile)
    evidence = [
        f"日支夫妻宫为{fp['day_branch']}，主气五行为{fp['spouse_palace_element'] or '待确认'}。",
        f"夫妻宫藏干对应十神为{'、'.join(fp['spouse_palace_hidden_ten_gods']) or '暂未读取'}。",
        f"{profile.get('gender', '未填性别')}命重点参考{star_label}，当前{star_label}数量为{star_count}。",
        f"命局较突出的关系相关标签为：{'、'.join(fp['love_pattern_tags'])}。",
    ]
    if fp["has_strong_peer"]:
        evidence.append("比劫较明显，关系中自我边界、平等感、朋友同辈和竞争意识更容易被放大。")
    if fp["has_strong_output"]:
        evidence.append("食伤较明显，表达、情绪反馈、审美期待和沟通方式会影响关系体验。")
    if fp["has_strong_officer_killing"]:
        evidence.append("官杀较明显，责任、承诺、规则和压力议题更容易进入关系。")
    if fp["has_strong_resource"]:
        evidence.append("印星较明显，安全感、理解、照顾、精神支持和稳定环境较重要。")
    return evidence


def _relationship_pattern(fp: dict, profile: dict) -> str:
    """感情模式。"""
    star_label = _partner_star_label(profile)
    star_count = _partner_star_count(fp, profile)
    if fp["has_strong_peer"] and fp["has_strong_output"]:
        return "自主表达型关系模式：既需要个人空间，也需要高质量沟通，容易在话语方式和边界上拉扯。"
    if fp["has_strong_peer"] and fp["has_strong_officer_killing"]:
        return "边界责任拉扯型关系模式：关系里既需要承诺，也需要保留自主空间，容易围绕主导权和责任分配拉扯。"
    if profile.get("gender") == "女" and fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        return "现实责任并重型关系模式：既看重承诺与担当，也容易把生活经营、资源安排和现实压力带入关系。"
    if profile.get("gender") == "女" and fp["has_strong_officer_killing"] and fp["spouse_palace_element"] == "水":
        return "压力安全感型关系模式：容易重视稳定承诺，但也需要分清真正的安全感和外界压力。"
    if fp["has_strong_officer_killing"] and profile.get("gender") == "女":
        return "责任承诺型关系模式：容易重视稳定、规则和对方担当，也要避免把压力等同于安全感。"
    if fp["has_strong_wealth"] and profile.get("gender") == "男":
        return "现实经营型关系模式：容易通过投入、安排、资源和生活经营表达关系态度。"
    if fp["has_strong_resource"]:
        return "安全感支持型关系模式：重视理解、陪伴、稳定环境和精神支撑。"
    if star_count == 0:
        return f"{star_label}不明显，感情更适合慢观察、慢确认，不宜只凭短期吸引推进承诺。"
    return "渐进磨合型关系模式：适合从相处质量、现实安排和共同成长中慢慢建立稳定感。"


def _love_differentiator(fp: dict, profile: dict) -> str:
    """根据命盘指纹生成差异化婚恋策略。"""
    star_label = _partner_star_label(profile)
    star_count = _partner_star_count(fp, profile)
    counts = (
        f"{star_label}{star_count}、财星{fp['wealth_star_count']}、官杀{fp['officer_star_count']}、"
        f"食伤{fp['output_star_count']}、比劫{fp['peer_star_count']}"
    )
    if profile.get("gender") == "女" and fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        strategy = (
            "此盘关系容易把承诺、生活经营和现实资源放在一起考量。"
            "适合找责任感清楚、财务观念稳定、能共同规划生活的人；风险在于把压力、控制或现实条件误认为稳定。"
        )
    elif profile.get("gender") == "女" and fp["has_strong_officer_killing"]:
        strategy = (
            "此盘伴侣星强，关系中容易被责任感、承诺感、规则感吸引。"
            "适合慢慢确认对方是否真正可靠，而不是只看外在标准；风险在于关系压力过早压过真实感受。"
        )
    elif profile.get("gender") == "男" and fp["has_strong_wealth"]:
        strategy = (
            "此盘男命财星明显，关系常通过现实投入、生活安排和资源经营来表达。"
            "适合把付出变成共同计划，也要避免只用资源投入代替情绪沟通。"
        )
    elif fp["has_strong_peer"] and fp["has_strong_output"]:
        strategy = (
            "此盘比劫与食伤同时明显，关系里既要空间，也要表达和反馈。"
            "现实中适合把想法、感受、朋友边界说具体；风险在于话说太快、太直接，或合作边界含糊。"
        )
    elif fp["has_strong_peer"] and fp["has_strong_officer_killing"]:
        strategy = (
            "此盘比劫与官杀同时明显，关系里容易同时出现自主需求和责任压力。"
            "现实中适合把谁主导、谁承担、怎样分工说清楚；风险在于一边想独立，一边又被承诺和规则牵动。"
        )
    elif fp["has_strong_peer"]:
        strategy = (
            "此盘比劫明显，关系中的自我边界、朋友同辈和独立性很重要。"
            "适合先谈清空间、金钱、人情和合作边界，再推进长期承诺。"
        )
    else:
        strategy = (
            "此盘关系适合在相处质量中慢慢观察，不宜只用单一流年或单一十神定性。"
        )
    return (
        f"差异化关系依据：夫妻宫{fp['day_branch']}，五行为{fp['spouse_palace_element']}，"
        f"藏干十神为{'、'.join(fp['spouse_palace_hidden_ten_gods']) or '暂未读取'}；{counts}。{strategy}"
    )


def _partner_types(fp: dict, profile: dict) -> list[str]:
    """适合伴侣类型。"""
    types: list[str] = []
    if fp["has_strong_resource"]:
        types.extend(["情绪稳定", "愿意理解支持", "重视长期安全感"])
    if fp["has_strong_officer_killing"]:
        types.extend(["有责任感", "规则感清楚", "能共同承担现实压力"])
    if fp["has_strong_wealth"]:
        types.extend(["现实感强", "会经营生活", "重视资源和计划"])
    if fp["has_strong_output"]:
        types.extend(["愿意沟通", "能欣赏表达和创意", "情绪反馈清楚"])
    if fp["has_strong_peer"]:
        types.extend(["尊重边界", "独立成熟", "不控制对方节奏"])
    if profile.get("gender") == "女" and fp["officer_star_count"] >= 3:
        types.append("承诺意识较强")
    if profile.get("gender") == "男" and fp["wealth_star_count"] >= 3:
        types.append("能共同经营现实生活")
    return list(dict.fromkeys(types))[:7] or ["稳定沟通", "边界清楚", "愿意共同成长"]


def _strengths(fp: dict) -> list[str]:
    """恋爱优势。"""
    strengths = []
    if fp["has_strong_output"]:
        strengths.append("表达和体验感较强，容易通过陪伴、分享、作品或生活情趣增加吸引力。")
    if fp["has_strong_wealth"]:
        strengths.append("现实经营意识较强，容易关注生活安排、资源投入和共同目标。")
    if fp["has_strong_officer_killing"]:
        strengths.append("责任感和承诺意识较强，适合把关系落到现实安排。")
    if fp["has_strong_resource"]:
        strengths.append("理解和支持需求明显，也容易在关系中提供照顾和稳定感。")
    if fp["has_strong_peer"]:
        strengths.append("独立性较强，关系中不容易完全失去自我。")
    return strengths or ["关系优势在于可通过稳定沟通和现实磨合逐步累积信任。"]


def _risks(fp: dict, profile: dict) -> list[str]:
    """关系风险。"""
    risks = []
    if profile.get("gender") == "女" and fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        risks.append("财官同现时，容易把现实条件、资源投入和责任承诺混在一起，需要区分感情稳定与现实压力。")
    elif profile.get("gender") == "女" and fp["has_strong_officer_killing"] and fp["spouse_palace_element"] == "水":
        risks.append("夫妻宫水而官杀强时，容易因安全感、承诺标准或外界评价感到压力，需要确认关系是否真正滋养自己。")
    if fp["has_strong_peer"]:
        risks.append("自我边界强时，容易因为谁主导、谁让步、谁付出更多而拉扯。")
    if fp["has_strong_output"]:
        risks.append("表达欲强时，容易话说太快或太直，造成误会。")
    if fp["has_strong_officer_killing"]:
        risks.append("责任压力强时，容易把关系变成标准、考核或控制。")
    if fp["has_strong_resource"]:
        risks.append("安全感需求强时，容易期待对方理解但没有说清楚。")
    if profile.get("gender") == "男" and fp["wealth_star_count"] == 0:
        risks.append("男命财星不明显时，关系投入和现实经营需要后天主动学习。")
    if profile.get("gender") == "女" and fp["officer_star_count"] == 0:
        risks.append("女命官杀不明显时，承诺节奏更适合慢确认，不宜被外界催促。")
    return risks or ["关系风险主要在于期待没有说清、边界没有说清和现实安排没有落地。"]


def _communication(fp: dict) -> str:
    """沟通建议。"""
    if fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        return "谈关系时把感情承诺、金钱安排、生活分工分开讨论，避免所有压力都压在同一次沟通里。"
    if fp["has_strong_officer_killing"] and fp["spouse_palace_element"] == "水":
        return "谈承诺前先确认自己的真实感受，不把对方外在条件、规则感或压力感直接等同于安全感。"
    if fp["has_strong_output"]:
        return "先表达事实，再表达感受，最后提出可执行请求，避免在情绪高点直接定性对方。"
    if fp["has_strong_peer"]:
        return "把个人空间、金钱边界、朋友往来和共同责任提前说清楚。"
    if fp["has_strong_officer_killing"]:
        return "谈承诺和责任时，也要同步谈压力、感受和可承受节奏。"
    if fp["has_strong_resource"]:
        return "不要只等对方猜到需求，建议把安全感需求说成具体行动。"
    return "把感受、需求、边界和现实安排分开说，少用猜测代替确认。"


def _action_plan(fp: dict, profile: dict) -> list[str]:
    """关系行动计划。"""
    actions = [
        f"围绕夫妻宫{fp['day_branch']}和{'、'.join(fp['love_pattern_tags'][:3])}观察真实相处模式。",
        f"重点参考{_partner_star_label(profile)}数量和夫妻宫藏干，不用单一流年判断关系结果。",
        _communication(fp),
    ]
    if fp["has_strong_peer"]:
        actions.append("涉及合伙、朋友、人情和金钱时，关系内要提前建立边界。")
    if fp["has_strong_output"]:
        actions.append("重要沟通先写下重点，避免表达过快造成误解。")
    if fp["has_strong_officer_killing"]:
        actions.append("把责任和承诺拆成双方都能执行的小安排。")
    if fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        actions.append("讨论长期关系时同步核对金钱观、生活规划和共同责任。")
    elif fp["has_strong_officer_killing"] and fp["spouse_palace_element"] == "水":
        actions.append("确认对方是否能提供稳定陪伴，而不是只提供规则、标准或外在压力。")
    return actions[:6]


def generate_love_report(chart: dict, profile: dict | None = None) -> dict:
    """
    生成婚恋专项报告。
    """
    profile = profile or {}
    fp = build_chart_fingerprint(chart)
    signature = build_chart_signature_text(chart, "婚恋专项差异依据")
    evidence = _evidence(fp, profile)
    relationship_pattern = _relationship_pattern(fp, profile)
    love_differentiator = _love_differentiator(fp, profile)
    suitable_partner_type = _partner_types(fp, profile)
    relationship_strengths = _strengths(fp)
    relationship_risks = _risks(fp, profile)
    communication_advice = _communication(fp)
    if fp["has_strong_officer_killing"] and fp["has_strong_wealth"]:
        next_3_years = [
            f"第一阶段重点观察夫妻宫{fp['day_branch']}是否引出现实经营和生活安排议题。",
            "第二阶段适合把金钱观、居住规划、家庭责任和共同目标逐项谈清楚。",
            "第三阶段再判断这段关系能否在现实压力下保持互相支持，而不是只靠责任感维系。",
        ]
    elif fp["has_strong_officer_killing"] and fp["spouse_palace_element"] == "水":
        next_3_years = [
            f"第一阶段重点观察夫妻宫{fp['day_branch']}带来的安全感、边界和情绪流动。",
            "第二阶段不急着被承诺推进，先看对方是否稳定、透明、能照顾真实感受。",
            "第三阶段再判断责任感是否转化为稳定陪伴，而不是持续压力。",
        ]
    else:
        next_3_years = [
            f"第一阶段先观察夫妻宫{fp['day_branch']}代表的相处主题是否被流年冲动。",
            f"第二阶段重点处理{'、'.join(fp['love_pattern_tags'][:3])}带来的关系议题。",
            f"第三阶段再看{_partner_star_label(profile)}数量{_partner_star_count(fp, profile)}对应的承诺、投入和现实安排是否稳定。",
        ]
    action_plan = _action_plan(fp, profile)
    sections = [
        _section("婚恋专项差异依据", signature),
        _section("命盘依据", " ".join(evidence)),
        _section("感情模式", relationship_pattern),
        _section("差异化关系策略", love_differentiator),
        _section("适合伴侣类型", "、".join(suitable_partner_type)),
        _section("恋爱优势", " ".join(relationship_strengths)),
        _section("关系压力点", " ".join(relationship_risks)),
        _section("夫妻宫分析", f"日支夫妻宫为{fp['day_branch']}，主气五行为{fp['spouse_palace_element']}，藏干十神为{'、'.join(fp['spouse_palace_hidden_ten_gods']) or '暂未读取'}。"),
        _section("男命财星 / 女命官杀", f"{profile.get('gender', '未填性别')}命重点参考{_partner_star_label(profile)}，当前数量为{_partner_star_count(fp, profile)}。"),
        _section("未来三年关系趋势", " ".join(next_3_years)),
        _section("沟通建议", communication_advice),
    ]
    return {
        "title": "婚恋专项报告",
        "evidence": evidence,
        "love_identity": relationship_pattern,
        "love_evidence": evidence,
        "relationship_pattern": relationship_pattern,
        "love_differentiator": love_differentiator,
        "chart_signature": signature,
        "suitable_partner_type": suitable_partner_type,
        "relationship_strengths": relationship_strengths,
        "relationship_risks": relationship_risks,
        "communication_advice": communication_advice,
        "next_3_years": next_3_years,
        "action_plan": action_plan,
        "sections": sections,
        "advice": " ".join(action_plan),
        "disclaimer": DISCLAIMER,
    }
