"""十神词条 —— 每个十神的中文解释、性格影响、职业倾向、行动建议。"""

from __future__ import annotations

TEN_GOD_EXPLANATIONS: dict[str, dict[str, str]] = {
    "正官": {
        "meaning": "正官代表正直、责任、自律与权威。它是克制日主的力量，但阴阳相异，属于正面的约束。",
        "personality": "为人正直守信，做事有条理，注重规则和秩序。有领导潜质和责任心，但也容易自我约束过强。",
        "career": "适合管理、公务员、法律、教育、审计、质检等需要规则意识和责任感的职业。",
        "advice": "发挥责任感和规则意识的同时，注意培养灵活性和包容心，避免过于刻板。",
    },
    "七杀": {
        "meaning": "七杀代表魄力、竞争、压力与突破。它是克制力最强的十神，象征非常规的力量。",
        "personality": "果断有冲劲，敢于挑战权威，不循规蹈矩。在压力下能爆发出更强能力，但容易急躁或与人冲突。",
        "career": "适合创业、管理、军警、外科医生、工程师、竞技体育等需要决断力和抗压能力的职业。",
        "advice": "善用魄力推动事业，注意控制冲动。七杀有制化为权威，无制则易生是非。",
    },
    "正印": {
        "meaning": "正印代表学识、长辈、贵人与庇护。它是生助日主的力量，属于温和的滋养。",
        "personality": "重视学习和修养，领悟力和记忆力不错。为人仁慈包容，容易得到长辈和贵人的帮助。",
        "career": "适合教育、研究、文化、医疗、咨询、慈善等需要知识和关怀的职业。",
        "advice": "发挥学习能力和贵人运，同时注意培养独立判断和行动力。",
    },
    "偏印": {
        "meaning": "偏印代表特殊才能、偏门学问与深度思考。属于偏门的滋养。",
        "personality": "思维独特有深度，喜欢钻研冷门或非常规领域。直觉敏锐，但有时显得孤僻或不合群。",
        "career": "适合科研、哲学、心理学、玄学、艺术创作、IT技术等需要深度思考和原创能力的职业。",
        "advice": "善用独特的思维方式和直觉力，注意拓宽社交面，避免钻牛角尖。",
    },
    "正财": {
        "meaning": "正财代表稳定的财富来源、正职收入与务实心态。",
        "personality": "务实稳重，注重实际收益和物质保障。理财方式偏保守，适合长期积累。",
        "career": "适合财务、会计、银行、商贸、地产、实体产业等需要稳健经营的职业。",
        "advice": "发挥务实和稳健的特质，适当关注新兴机会，避免过于保守错失良机。",
    },
    "偏财": {
        "meaning": "偏财代表投资、横财、商业头脑与人脉资源。属于流动性的财富。",
        "personality": "商业嗅觉敏锐，善于发现机会，社交能力强。花钱大方，但容易有财务波动。",
        "career": "适合投资、贸易、营销、公关、中介、创业等需要资源整合的职业。",
        "advice": "发挥商业和社交天赋，注意财务规划和风险控制，避免过度投机。",
    },
    "食神": {
        "meaning": "食神代表才华、享受、口福与创造力。属于温和的释放。",
        "personality": "性格温和乐观，有艺术天赋和审美力。喜欢美食和生活品质，心态好。",
        "career": "适合艺术、设计、餐饮、娱乐、表演、写作、教育培训等需要创造力的职业。",
        "advice": "发挥才华和创造力，善用温和的沟通方式，注意保持行动力。",
    },
    "伤官": {
        "meaning": "伤官代表创意、表达、叛逆与非凡才华。属于激情的释放。",
        "personality": "聪明敏锐，表达力强，有独特的审美和创意。不喜被约束，个性鲜明。",
        "career": "适合艺术、设计、传媒、广告、编剧、科技创业等需要创新和表达的职业。",
        "advice": "发挥才华的同时注意收敛锋芒。伤官有制化为才华，无制易生口舌。",
    },
    "比肩": {
        "meaning": "比肩代表自我、朋友、合伙与竞争。是日主的同类力量。",
        "personality": "独立自主，有主见和自尊心。重视朋友，但容易有竞争心理，不太愿意示弱。",
        "career": "适合自主创业、合伙经营、体育竞技、销售等需要独立性和竞争意识的职业。",
        "advice": "善用独立和自主的优势，注意团队协作，学会借力而不是凡事自己扛。",
    },
    "劫财": {
        "meaning": "劫财代表社交、竞争、破财与共享。是另一种形式的同类力量。",
        "personality": "社交活跃，朋友多，讲义气重感情。但容易因朋友关系产生财务消耗。",
        "career": "适合社交型、公关、中介、社团管理、公益组织等需要人际交往的职业。",
        "advice": "发挥社交和人脉优势，注意财务边界，避免因义气导致不必要的经济损失。",
    },
}


def get_ten_god_explanation(ten_god: str) -> dict[str, str]:
    return TEN_GOD_EXPLANATIONS.get(ten_god, {})


def get_ten_god_summary(ten_god: str) -> str:
    info = TEN_GOD_EXPLANATIONS.get(ten_god, {})
    return info.get("meaning", "") if info else ""


def get_ten_god_html(ten_god: str) -> str:
    info = get_ten_god_explanation(ten_god)
    if not info:
        return ""
    p = info["personality"]
    c = info["career"]
    a = info["advice"]
    m = info["meaning"]
    return (
        f'<div style="font-weight:600;color:#3D2B1A;font-size:15px;margin-bottom:6px;">{ten_god}</div>'
        f'<p style="color:#5C4A32;font-size:13px;margin:0 0 8px 0;line-height:1.6;">{m}</p>'
        f'<div style="font-size:12px;color:#5C4A32;line-height:1.7;">'
        f'<strong>性格：</strong>{p}<br>'
        f'<strong>职业：</strong>{c}<br>'
        f'<strong>建议：</strong>{a}'
        f'</div>'
    )
