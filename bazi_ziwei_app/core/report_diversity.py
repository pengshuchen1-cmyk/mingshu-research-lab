"""报告差异化辅助文本。

把命盘真实结构转成用户能看懂、且足够区分不同八字的依据文本。
这些内容用于命局总论、命盘类型、命盘总览和综合问盘，避免只套等级模板。
"""

from __future__ import annotations

from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.chart_fingerprint import build_chart_fingerprint
from core.chart_facts import chart_facts_from_chart


TEN_GOD_ORDER = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"]
SOURCE_TEXT = "参考传统子平法中十神旺衰、格局取用与五行调候的综合思路。"


def _join(items: list[str], default: str = "暂不明显") -> str:
    return "、".join([str(item) for item in items if item]) or default


def _pillar_line(chart: dict) -> str:
    pillars = chart.get("pillars", {})
    labels = [("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")]
    parts = []
    for key, label in labels:
        pillar = pillars.get(key, {})
        text = pillar.get("pillar") or f"{pillar.get('gan', '')}{pillar.get('zhi', '')}"
        if text:
            parts.append(f"{label}{text}")
    month_zhi = pillars.get("month", {}).get("zhi", "")
    day_zhi = pillars.get("day", {}).get("zhi", "")
    hour_zhi = pillars.get("hour", {}).get("zhi", "")
    extra = []
    if month_zhi:
        extra.append(f"月令{month_zhi}{BRANCH_MAIN_ELEMENTS.get(month_zhi, '')}")
    if day_zhi:
        extra.append(f"夫妻宫{day_zhi}{BRANCH_MAIN_ELEMENTS.get(day_zhi, '')}")
    if hour_zhi:
        extra.append(f"时支{hour_zhi}{BRANCH_MAIN_ELEMENTS.get(hour_zhi, '')}")
    return f"四柱依据：{'｜'.join(parts)}；{_join(extra)}。"


def _profile_line(chart: dict) -> str:
    profile = chart.get("profile", {}) or {}
    name = profile.get("name", "未命名")
    gender = profile.get("gender", "性别未填")
    birth_date = profile.get("birth_date", "日期未填")
    hour = profile.get("birth_hour", "")
    minute = profile.get("birth_minute", "")
    place = profile.get("birth_place", "")
    time_text = ""
    if hour != "":
        try:
            time_text = f"{int(hour):02d}:{int(minute or 0):02d}"
        except Exception:
            time_text = str(hour)
    location = f"，出生地{place}" if place else ""
    return f"出生校验：{name}，{gender}，{birth_date} {time_text}{location}；时辰会影响时柱、长期规划、项目收尾和晚间状态判断。"


def _five_element_line(chart: dict) -> str:
    five_elements = chart.get("five_elements", {})
    if not five_elements:
        return "五行依据：暂未取得五行分数。"
    total = sum(float(score) for score in five_elements.values()) or 1
    ordered = sorted(five_elements.items(), key=lambda item: -float(item[1]))
    scores = [
        f"{element}{float(score):.1f}分/{float(score) / total * 100:.0f}%"
        for element, score in ordered
    ]
    strongest = ordered[0][0] if ordered else ""
    weakest = min(ordered, key=lambda item: float(item[1]))[0] if ordered else ""
    return f"五行依据：{'，'.join(scores)}；最明显是{strongest}，最需要留意补足的是{weakest}。"


def _ten_god_line(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    if not counts:
        return "十神依据：暂未取得十神统计。"
    detail = "，".join(f"{name}{int(counts.get(name, 0))}" for name in TEN_GOD_ORDER)
    wealth = int(counts.get("正财", 0)) + int(counts.get("偏财", 0))
    officer = int(counts.get("正官", 0)) + int(counts.get("七杀", 0))
    output = int(counts.get("食神", 0)) + int(counts.get("伤官", 0))
    resource = int(counts.get("正印", 0)) + int(counts.get("偏印", 0))
    peer = int(counts.get("比肩", 0)) + int(counts.get("劫财", 0))
    groups = f"财星{wealth}、官杀{officer}、食伤{output}、印星{resource}、比劫{peer}"
    top = sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[:3]
    top_text = "、".join(f"{name}{value}" for name, value in top if value)
    return f"十神依据：{detail}；分组看为{groups}；最突出的信号是{top_text or '暂不集中'}。"


def _plain_tendency(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    strength = chart.get("day_master_strength", {})
    groups = {
        "财星": int(counts.get("正财", 0)) + int(counts.get("偏财", 0)),
        "官杀": int(counts.get("正官", 0)) + int(counts.get("七杀", 0)),
        "食伤": int(counts.get("食神", 0)) + int(counts.get("伤官", 0)),
        "印星": int(counts.get("正印", 0)) + int(counts.get("偏印", 0)),
        "比劫": int(counts.get("比肩", 0)) + int(counts.get("劫财", 0)),
    }
    top_group = max(groups, key=groups.get) if groups else "综合"
    strength_label = strength.get("strength", "中和")
    readable = {
        "财星": "更容易把注意力放在收入、客户、资源、购买决策和现实回报上",
        "官杀": "更容易遇到规则、责任、职位要求、考核压力或管理议题",
        "食伤": "更适合把能力变成作品、表达、技术输出、内容或服务",
        "印星": "更需要学习系统、资质平台、贵人支持和稳定的知识框架",
        "比劫": "自我驱动力和同辈互动较明显，合作分账与边界要讲清楚",
    }
    if strength_label in ("身弱", "从弱"):
        mode = "这类命盘做事更适合先借平台、借规则、借专业方法，再逐步发力。"
    elif strength_label == "身强":
        mode = "这类命盘主动性较强，适合承担主导角色，但要避免过度硬扛。"
    else:
        mode = "这类命盘承接力相对中和，关键在于顺着阶段机会调整节奏。"
    return f"现实翻译：{readable.get(top_group, '需要综合看多个信号')}；{mode}"


def _source_focus(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    groups = {
        "财星": int(counts.get("正财", 0)) + int(counts.get("偏财", 0)),
        "官杀": int(counts.get("正官", 0)) + int(counts.get("七杀", 0)),
        "食伤": int(counts.get("食神", 0)) + int(counts.get("伤官", 0)),
        "印星": int(counts.get("正印", 0)) + int(counts.get("偏印", 0)),
        "比劫": int(counts.get("比肩", 0)) + int(counts.get("劫财", 0)),
    }
    top_group = max(groups, key=groups.get) if groups else ""
    focus = {
        "财星": "书籍取法：本盘以财星为重点，主要参考《渊海子平》财为养命之源、《三命通会》财星旺衰，以及《子平真诠》身财能否相配。",
        "官杀": "书籍取法：本盘以官杀压力为重点，主要参考《子平真诠》官杀取用、《三命通会》杀印制化，以及《渊海子平》官杀对责任规则的象意。",
        "食伤": "书籍取法：本盘以食伤输出为重点，主要参考《渊海子平》食伤泄秀、《子平真诠》食伤配合，以及《滴天髓阐微》才气流通的思路。",
        "印星": "书籍取法：本盘以印星资源为重点，主要参考《子平真诠》印星护身、《三命通会》印绶根气，以及《命理探源》学习资质的象意。",
        "比劫": "书籍取法：本盘以比劫同辈为重点，主要参考《渊海子平》比劫分财、《三命通会》兄弟朋友象，以及《神峰通考》旺衰取舍。",
    }
    return focus.get(top_group, SOURCE_TEXT)


def _day_master_profile(chart: dict) -> str:
    day_master = chart.get("day_master", "")
    day_element = STEM_ELEMENTS.get(day_master, "")
    strength_label = chart.get("day_master_strength", {}).get("strength", "中和")
    combo_text = {
        ("火", "从弱"): "火日主从弱时，不宜只靠热情硬冲；现实中更像小灯放在风雨里，要借规则、资源、职位平台和现实条件保护火苗。",
        ("火", "身弱"): "火日主身弱时，表达力需要被环境点燃，适合先积累作品、贵人和稳定场景，再逐步增加曝光。",
        ("火", "中和"): "火日主中和时，既能表达也能收住，适合在行动和复盘之间来回校准，避免只凭一阵热度做决定。",
        ("火", "身强"): "火日主身强时，行动、表达和领导欲更明显，适合主动争取舞台，但要留意急躁、面子和睡眠消耗。",
        ("水", "从弱"): "水日主从弱时，流动性被现实土火牵引，适合顺着责任、财务、项目和平台机会走，不宜长期停在犹豫里。",
        ("水", "身弱"): "水日主身弱时，信息和精力都要先蓄起来，适合减少无效奔波，把沟通、学习和休息节奏排稳。",
        ("水", "中和"): "水日主中和时，信息处理和资源调度较灵活，关键是把想法落到具体计划，不要只流动不沉淀。",
        ("水", "身强"): "水日主身强时，思路多、变化快、人脉流动强，适合做沟通资源型事务，但要防止方向过散。",
        ("土", "身强"): "土日主身强时，承载力和稳定性明显，适合管资源、管流程、做长期积累，但要避免固守旧经验。",
        ("土", "身弱"): "土日主身弱时，现实责任容易压身，适合先搭框架、找帮手、分阶段完成任务。",
        ("木", "身强"): "木日主身强时，成长欲和主见较明显，适合规划、教育、创意与开拓，但要修剪分支。",
        ("金", "身强"): "金日主身强时，规则感、执行力和取舍能力明显，适合技术、管理、金融或标准化事务。",
    }.get((day_element, strength_label))
    if combo_text:
        return f"{day_master}{day_element}日主画像：{combo_text}"
    text = {
        "木": "木日主像树木花草，重点不在一时爆发，而在方向、成长、学习和持续伸展。命局木弱时，要先找土壤和水源；木旺时，要学会修枝定形。",
        "火": "火日主像灯火阳光，现实中常表现为表达、热度、行动和被看见的需求。火弱时先要有人点灯和给资源；火旺时要避免急躁上头。",
        "土": "土日主像山地田园，重承载、稳定、现实结果和长期积累。土弱时要先建立规则与支撑；土旺时要避免反应过慢或被旧经验困住。",
        "金": "金日主像金属器物，重规则、边界、效率、技术和取舍。金弱时要靠制度和训练成形；金旺时要避免过度锋利，关系中要留余地。",
        "水": "水日主像江河雨露，重流动、信息、沟通、变化和资源调度。水弱时要补信息与休息；水旺时要避免想法太散或行动延迟。",
    }.get(day_element, "日主特质暂不明显，需要结合月令、藏干和大运继续判断。")
    return f"{day_master}{day_element}日主画像：{text}"


def _season_profile(chart: dict) -> str:
    month_zhi = chart.get("pillars", {}).get("month", {}).get("zhi", "")
    season = {
        "寅": "春初木气启动，事情容易从计划、学习、开端中生发。",
        "卯": "仲春木气纯粹，成长、表达和人际推进感会更明显。",
        "辰": "辰月湿土承接，现实事务、房产空间、资源整理意味较重。",
        "巳": "巳月火气渐旺，行动、曝光、竞争和情绪热度会被放大。",
        "午": "午月火势最明，适合主动表达，也要留意急躁与消耗。",
        "未": "未月燥土含火，事务容易落到责任、存量整理和现实承接。",
        "申": "申月金气启动，规则、技术、合同、车辆、流程类信号更明显。",
        "酉": "酉月金气纯粹，审美、规则、财务分账、精修和边界感突出。",
        "戌": "戌月燥土收束，旧账、房屋、项目收尾和责任复盘容易出现。",
        "亥": "亥月水气启动，信息、人脉、出行、暗线资源和情绪流动较多。",
        "子": "子月水势最重，思考、沟通、睡眠、流动变化和隐性压力更明显。",
        "丑": "丑月寒湿之土，财务沉淀、库存整理、健康保养和慢变量更突出。",
    }.get(month_zhi, "月令暂不明确，季节气势需要结合排盘继续判断。")
    return f"月令气候画像：{season}"


def _group_profile(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    groups = {
        "财星": int(counts.get("正财", 0)) + int(counts.get("偏财", 0)),
        "官杀": int(counts.get("正官", 0)) + int(counts.get("七杀", 0)),
        "食伤": int(counts.get("食神", 0)) + int(counts.get("伤官", 0)),
        "印星": int(counts.get("正印", 0)) + int(counts.get("偏印", 0)),
        "比劫": int(counts.get("比肩", 0)) + int(counts.get("劫财", 0)),
    }
    top_group = max(groups, key=groups.get) if groups else "综合"
    text = {
        "财星": "事情常落到钱、订单、客户、资产、购买、回款和资源交换上，做决定时要先算现金流，再谈扩张。",
        "官杀": "生活里较容易出现上级要求、制度压力、职位责任、证照审批和目标考核，越有规则越能减少内耗。",
        "食伤": "更适合靠作品、口才、技术、内容、方案和服务输出打开局面，表达越具体，机会越容易落地。",
        "印星": "学习、证书、贵人、平台、资料、系统方法是关键资源，先把方法论搭好，再谈速度会更稳。",
        "比劫": "朋友同事、同行竞争、合伙分工、人情往来会被放大，越早讲清边界，越能保护收益和关系。",
    }.get(top_group, "多个信号接近，需要把事业、财务、关系分开判断。")
    return f"十神现实画像：本盘{top_group}{groups.get(top_group, 0)}个，{text}"


def _spouse_profile(chart: dict) -> str:
    day_zhi = chart.get("pillars", {}).get("day", {}).get("zhi", "")
    element = BRANCH_MAIN_ELEMENTS.get(day_zhi, "")
    branch_text = {
        "子": "关系中容易有情绪流动、距离感、信息沟通和安全感议题。",
        "丑": "关系更看重现实照顾、财务安排、生活稳定和长期耐心。",
        "寅": "伴侣关系需要成长空间，容易因事业方向、学习计划或外部机会而变化。",
        "卯": "关系里审美、感受、陪伴和表达很重要，也要避免只凭感觉判断。",
        "辰": "关系常牵涉房屋、家庭资源、现实责任或旧事整理。",
        "巳": "关系热度较强，吸引力明显，但要注意急躁、占有和沟通火气。",
        "午": "关系外显度高，适合坦诚表达，也要留意情绪上头和面子问题。",
        "未": "关系需要照顾现实细节，容易把家庭、责任、资源承接放在一起看。",
        "申": "关系中规则、距离、工作安排和沟通效率很关键。",
        "酉": "关系重边界、审美和承诺质量，容易在细节和标准上较敏感。",
        "戌": "关系容易进入责任复盘、旧问题处理和居住安排的主题。",
        "亥": "关系带有流动、人情、远方或内心感受的因素，需要避免想太多不说清。",
    }.get(day_zhi, "夫妻宫暂不明确，关系部分需要结合大运流年引动。")
    return f"夫妻宫画像：日支{day_zhi}{element}，{branch_text}"


def _strength_profile(chart: dict) -> str:
    strength = chart.get("day_master_strength", {})
    label = strength.get("strength", "中和")
    favorable = _join(list(strength.get("favorable_elements", [])), "阶段环境")
    unfavorable = _join(list(strength.get("unfavorable_elements", [])), "过度消耗")
    text = {
        "身强": f"身强盘像发动机马力足，适合主动争取、承担主责、打开局面；但遇到{unfavorable}过多时，容易变成硬扛、急进或不愿求助。",
        "身弱": f"身弱盘像设备需要稳定供电，重点不是硬冲，而是先找{favorable}代表的资源、平台、学习和帮手，再把事情做稳。",
        "从弱": f"从弱盘更像顺水行舟，硬要补回日主未必舒服，反而要顺着{favorable}代表的环境、规则、资源和现实机会去借势。",
        "中和": f"中和盘像车身较平衡，能进能退，关键是看阶段风向；遇到{favorable}可主动推进，遇到{unfavorable}则先收缩节奏。",
    }.get(label, "强弱暂不明时，先把现实反馈当成校准依据。")
    return f"强弱打法画像：{text}"


def _gender_profile(chart: dict) -> str:
    profile = chart.get("profile", {}) or {}
    gender = profile.get("gender", "")
    counts = chart.get("ten_god_counts", {})
    if gender == "男":
        wealth = int(counts.get("正财", 0)) + int(counts.get("偏财", 0))
        return (
            f"性别取象：男命关系多看财星，本盘财星{wealth}个。"
            "现实里会更在意伴侣关系中的实际安排、共同资源、花费分配和生活经营。"
            "若财星同时被流年或流月引动，常见表现不是单纯桃花，而是客户订单、项目回款、伴侣消费、房车店铺、大件添置、合伙分账等现实议题一起出现。"
            "判断时要把感情、钱和资源分开看：感情看承诺与相处，财务看预算与边界，资产看合同与长期压力。"
        )
    if gender == "女":
        officer = int(counts.get("正官", 0)) + int(counts.get("七杀", 0))
        return (
            f"性别取象：女命关系多看官杀，本盘官杀{officer}个。"
            "现实里更容易把责任感、承诺质量、规则边界和对方担当作为关系判断重点。"
            "若官杀被大运流年流月引动，常见表现包括上级要求、考核审批、职位压力、伴侣标准、合同责任、交通规则、身体压力信号等。"
            "判断时要把人和压力分开看：关系看对方是否可靠，事业看规则是否清楚，身体看压力有没有长期积累。"
        )
    return "性别取象：未填写性别时，关系判断先以夫妻宫、桃花和大运引动为主。"


def _top_ten_god_story(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    top_items = [(name, int(value)) for name, value in sorted(counts.items(), key=lambda item: (-int(item[1]), item[0])) if int(value) > 0][:3]
    meaning = {
        "比肩": "比肩多时，自我推进、同辈竞争、朋友同事影响会变强，适合独立承担，但合伙要讲规则。",
        "劫财": "劫财明显时，人情支出、朋友求助、资源分配和临时合作更容易出现，要先说清钱和责任。",
        "食神": "食神代表稳定输出、作品打磨、技能成果和生活享受，适合把能力做成可交付的服务。",
        "伤官": "伤官代表表达突破、创意释放、规则摩擦和汇报展示，适合创新，但说话要留余地。",
        "正财": "正财代表稳定收入、预算、客户订单、采购回款和现实事务，适合稳扎稳打地积累。",
        "偏财": "偏财代表项目机会、临时收入、资源变现和外部财路，适合灵活捕捉，但要防冲动投入。",
        "正官": "正官代表责任、职位、流程、审批、考试和上级要求，适合在规则清楚的环境里建立信用。",
        "七杀": "七杀代表竞争、高压任务、突发挑战和执行突破，适合在目标明确时冲刺，但要管理压力。",
        "正印": "正印代表学习、证书、贵人、稳定平台和保护系统，适合靠专业资质慢慢抬高上限。",
        "偏印": "偏印代表研究、灵感、独立思考、非标方法和专业深度，适合做需要钻研的领域。",
    }
    if not top_items:
        return "前三十神画像：十神分布不集中，现实事件需要结合大运流年逐步观察。"
    parts = [f"{name}{count}个：{meaning.get(name, '需要结合位置继续判断')}" for name, count in top_items]
    return "前三十神断事线索：" + " ".join(parts)


def _position_ten_god_story(chart: dict) -> str:
    ten_gods = chart.get("ten_gods", {})
    hidden_stems = chart.get("hidden_stems", {})
    labels = {
        "year": "年柱外部环境",
        "month": "月柱事业主线",
        "day": "日柱自我关系",
        "hour": "时柱长期规划",
    }
    plain = {
        "比肩": "同辈、自主、竞争",
        "劫财": "人情、合伙、分账",
        "食神": "作品、技能、稳定输出",
        "伤官": "表达、突破、规则摩擦",
        "正财": "稳定收入、订单、现实经营",
        "偏财": "项目机会、资源变现、临时财路",
        "正官": "责任、职位、流程、承诺",
        "七杀": "压力、竞争、突发任务",
        "正印": "学习、贵人、平台保护",
        "偏印": "研究、灵感、非标方法",
    }
    parts = []
    for key in ("year", "month", "day", "hour"):
        gan_god = ten_gods.get(key, {}).get("gan", "")
        hidden = [item.get("ten_god", "") for item in hidden_stems.get(key, []) if item.get("ten_god")]
        signals = [gan_god, *hidden[:2]]
        readable = "、".join(f"{god}({plain.get(god, '需细看')})" for god in signals if god)
        if readable:
            parts.append(f"{labels[key]}见{readable}")
    return "十神落位断事：" + "；".join(parts) + "。"


def _event_focus_profile(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    groups = {
        "财星": int(counts.get("正财", 0)) + int(counts.get("偏财", 0)),
        "官杀": int(counts.get("正官", 0)) + int(counts.get("七杀", 0)),
        "食伤": int(counts.get("食神", 0)) + int(counts.get("伤官", 0)),
        "印星": int(counts.get("正印", 0)) + int(counts.get("偏印", 0)),
        "比劫": int(counts.get("比肩", 0)) + int(counts.get("劫财", 0)),
    }
    top_group = max(groups, key=groups.get) if groups else ""
    events = {
        "财星": "事件焦点偏财务资源：项目回款、客户订单、预算采购、房子店铺、车辆大件、合伙分账和现金流安排会更值得跟踪。",
        "官杀": "事件焦点偏规则压力：合同审批、岗位调整、上级要求、交通合规、考试证照、伴侣承诺和身体压力信号会更值得跟踪。",
        "食伤": "事件焦点偏输出表达：汇报展示、内容发布、技术交付、口舌误会、作品打磨、培训教学和创意变现会更值得跟踪。",
        "印星": "事件焦点偏学习保护：证书资料、贵人平台、休整恢复、长辈帮助、房屋文书、系统搭建和专业研究会更值得跟踪。",
        "比劫": "事件焦点偏同辈边界：朋友求助、同事竞争、团队摩擦、合伙分工、人情酒局、分账争议和资源互换会更值得跟踪。",
    }
    return events.get(top_group, "事件焦点需要结合大运流年继续观察。")


def _element_event_profile(chart: dict) -> str:
    five_elements = chart.get("five_elements", {})
    if not five_elements:
        return "五行事件取象：五行分数不足，暂不展开事件侧重点。"
    strongest = max(five_elements, key=lambda key: float(five_elements.get(key, 0)))
    weakest = min(five_elements, key=lambda key: float(five_elements.get(key, 0)))
    strong_events = {
        "木": "学习成长、规划扩张、文书教育、肝胆筋骨和人际生发",
        "火": "曝光表达、名气热度、酒局应酬、睡眠情绪、电子设备和急躁上火",
        "土": "房子店铺、土地空间、脾胃代谢、库存旧账、家庭责任和稳定承接",
        "金": "合同规则、车辆器械、金融分账、皮肤呼吸、审美精修和执行边界",
        "水": "出行流动、信息沟通、酒水夜间、腰肾精力、暗线资源和情绪波动",
    }
    weak_events = {
        "木": "木弱时计划和成长动力要靠后天补足，容易需要外部提醒来启动",
        "火": "火弱时曝光和行动热度不足，适合先预热，不宜临时硬冲",
        "土": "土弱时承接力和稳定感不足，房屋、脾胃、预算和存量事务要慢慢补",
        "金": "金弱时规则、合同、车辆器械、边界和执行标准要特别写清",
        "水": "水弱时沟通、休息、出行节奏和精力恢复要留余量",
    }
    return f"五行事件取象：{strongest}最旺，容易牵动{strong_events.get(strongest, '相关事件')}；{weakest}最弱，{weak_events.get(weakest, '需要后天补足')}。"


def _risk_action_profile(chart: dict) -> str:
    counts = chart.get("ten_god_counts", {})
    groups = {
        "财星": int(counts.get("正财", 0)) + int(counts.get("偏财", 0)),
        "官杀": int(counts.get("正官", 0)) + int(counts.get("七杀", 0)),
        "食伤": int(counts.get("食神", 0)) + int(counts.get("伤官", 0)),
        "印星": int(counts.get("正印", 0)) + int(counts.get("偏印", 0)),
        "比劫": int(counts.get("比肩", 0)) + int(counts.get("劫财", 0)),
    }
    top_group = max(groups, key=groups.get) if groups else ""
    text = {
        "财星": "行动抓手：先做预算表、合同表和回款表；风险点在贪快扩张、朋友借钱、合伙账目不清和大件消费冲动。",
        "官杀": "行动抓手：先确认规则、期限、责任人和书面流程；风险点在压力堆积、违规驾驶、合同遗漏和把伴侣当成考核对象。",
        "食伤": "行动抓手：先把作品、方案、报价和交付清单列出来；风险点在说得太快、承诺太满、和上级规则硬碰硬。",
        "印星": "行动抓手：先补证书、资料、方法论和可靠平台；风险点在想太多、行动慢、依赖贵人或迟迟不做现实验证。",
        "比劫": "行动抓手：先约定分工、分账、边界和退出方式；风险点在人情酒局、朋友求助、同业竞争和合伙消耗。",
    }
    return text.get(top_group, "行动抓手：先记录现实反馈，再结合大运流年校准。")


def _monthly_calibration_profile(chart: dict) -> str:
    pillars = chart.get("pillars", {})
    month_zhi = pillars.get("month", {}).get("zhi", "")
    hour_zhi = pillars.get("hour", {}).get("zhi", "")
    calibration = {
        "子": "子水月令遇流月引动时，重点看夜间作息、酒水应酬、信息沟通、出行流动和情绪安全感。",
        "丑": "丑土月令遇流月引动时，重点看库存旧账、脾胃状态、储蓄预算、房屋角落和慢性事务。",
        "寅": "寅木月令遇流月引动时，重点看学习开端、项目启动、外出开拓、肝胆筋骨和计划变化。",
        "卯": "卯木月令遇流月引动时，重点看合作关系、审美形象、文书沟通、感情互动和柔性谈判。",
        "辰": "辰土月令遇流月引动时，重点看房产空间、旧账整理、复杂协调、湿土健康和资源仓库。",
        "巳": "巳火月令遇流月引动时，重点看曝光热度、技术设备、酒局应酬、急躁上火和快速变化。",
        "午": "午火月令遇流月引动时，重点看名气表达、情绪热度、交通速度、睡眠心火和公开行动。",
        "未": "未土月令遇流月引动时，重点看家庭责任、房屋店铺、脾胃代谢、存量整理和现实承接。",
        "申": "申金月令遇流月引动时，重点看车辆器械、合同规则、奔波差旅、技术执行和关系边界。",
        "酉": "酉金月令遇流月引动时，重点看财务分账、审美精修、合同细节、皮肤呼吸和承诺标准。",
        "戌": "戌土月令遇流月引动时，重点看项目收尾、房屋责任、旧问题复盘、燥土健康和长期承诺。",
        "亥": "亥水月令遇流月引动时，重点看远方人脉、暗线资源、情绪流动、睡眠恢复和想法变化。",
    }
    hour_focus = {
        "子": "时支子水提示长期规划里要留意睡眠、信息和夜间节奏。",
        "丑": "时支丑土提示长期规划里要留意储蓄、库存和慢性健康。",
        "寅": "时支寅木提示长期规划里适合学习开拓，也要注意筋骨拉伤。",
        "卯": "时支卯木提示长期规划里关系合作与审美表达会反复出现。",
        "辰": "时支辰土提示长期规划里房屋空间、旧账和资源整合重要。",
        "巳": "时支巳火提示长期规划里曝光、技术、应酬和急躁风险要管理。",
        "午": "时支午火提示长期规划里名气表达、交通速度和睡眠心火要管理。",
        "未": "时支未土提示长期规划里家庭责任、店铺空间和脾胃状态要管理。",
        "申": "时支申金提示长期规划里车辆、合同、技术工具和奔波变化重要。",
        "酉": "时支酉金提示长期规划里财务分账、审美标准和关系边界重要。",
        "戌": "时支戌土提示长期规划里项目收尾、房产责任和旧问题复盘重要。",
        "亥": "时支亥水提示长期规划里远方人脉、暗线资源和情绪流动重要。",
    }
    return f"流月校准入口：{calibration.get(month_zhi, '月令需结合流月继续观察')} {hour_focus.get(hour_zhi, '')}"


def _pillar_story(chart: dict) -> str:
    pillars = chart.get("pillars", {})
    stem_words = {
        "甲": "像大树，重原则、方向和长期生长",
        "乙": "像藤花，重适应、审美和细腻协作",
        "丙": "像太阳，重表达、热度和公开行动",
        "丁": "像灯烛，重灵感、感受和精细照明",
        "戊": "像高山，重承载、稳定和现实责任",
        "己": "像田园，重照顾、资源整理和细水长流",
        "庚": "像矿铁，重执行、规则和直接处理问题",
        "辛": "像珠玉，重标准、质感和边界分寸",
        "壬": "像江河，重流动、信息和资源调度",
        "癸": "像雨露，重敏感、滋养和暗中酝酿",
    }
    branch_words = {
        "子": "子水主信息、情绪、安全感和夜间状态",
        "丑": "丑土主积蓄、库存、慢性事务和身体保养",
        "寅": "寅木主开端、学习、远行和主动开拓",
        "卯": "卯木主关系、审美、合作和柔性推进",
        "辰": "辰土主房屋、旧账、资源库和复杂协调",
        "巳": "巳火主曝光、技术、热度和快速变化",
        "午": "午火主名气、表达、情绪热度和行动力",
        "未": "未土主承接、家庭责任、现实细节和存量整理",
        "申": "申金主规则、车辆、合同、技术和奔波变化",
        "酉": "酉金主标准、财务、精修、审美和关系边界",
        "戌": "戌土主收尾、责任、房产空间和旧问题复盘",
        "亥": "亥水主人脉、远方、暗线资源和想法流动",
    }
    label_meaning = {
        "year": "早年环境/外部圈层",
        "month": "事业节奏/主线环境",
        "day": "自我与亲密关系",
        "hour": "长期规划/晚间状态",
    }
    label_cn = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
    parts = []
    for key in ("year", "month", "day", "hour"):
        item = pillars.get(key, {})
        gan = item.get("gan", "")
        zhi = item.get("zhi", "")
        if not gan and not zhi:
            continue
        parts.append(
            f"{label_cn[key]}看{label_meaning[key]}："
            f"{gan}{stem_words.get(gan, '天干信号需结合十神看')}，"
            f"{zhi}{branch_words.get(zhi, '地支信号需结合藏干看')}"
        )
    return "逐柱现实信号：" + "；".join(parts) + "。"


def project_chart_facts_for_report(chart: dict) -> dict:
    """Create the legacy-shaped read view exclusively from attached canonical facts."""
    facts_object = chart_facts_from_chart(chart)
    facts = facts_object.to_dict()
    projected = dict(chart)
    pillar_keys = ("year", "month", "day", "hour")
    pillar_texts = list(facts.get("pillars", []) or [])
    projected["pillars"] = {
        key: {
            "pillar": str(pillar_texts[index]) if index < len(pillar_texts) else "",
            "gan": str(pillar_texts[index])[:1] if index < len(pillar_texts) else "",
            "zhi": str(pillar_texts[index])[1:2] if index < len(pillar_texts) else "",
        }
        for index, key in enumerate(pillar_keys)
    }
    projected["day_master"] = str(facts.get("day_master", ""))
    projected["five_elements"] = dict(facts.get("element_counts", {}) or {})
    projected["ten_gods"] = facts.get("ten_gods", {}) or {}
    counts: dict[str, int] = {}
    for item in projected["ten_gods"].values():
        if not isinstance(item, dict):
            continue
        visible = item.get("gan")
        if visible and visible != "日主":
            counts[str(visible)] = counts.get(str(visible), 0) + 1
        for hidden in item.get("hidden_stems", []) or []:
            if isinstance(hidden, dict) and hidden.get("ten_god"):
                name = str(hidden["ten_god"])
                counts[name] = counts.get(name, 0) + 1
    projected["ten_god_counts"] = counts
    projected["hidden_stems"] = {
        key: list((projected["ten_gods"].get(key, {}) or {}).get("hidden_stems", []) or [])
        for key in pillar_keys
    }
    strength = facts.get("strength", {}) or {}
    projected["day_master_strength"] = {
        "strength": strength.get("classification", "暂无法判断"),
        "favorable_elements": list(strength.get("favorable_elements", [])),
        "unfavorable_elements": list(strength.get("unfavorable_elements", [])),
        "public_evidence": list(strength.get("evidence", [])),
        "net_score": 0.0,
    }
    projected["pattern_analysis"] = {
        "pattern": (facts.get("pattern", {}) or {}).get("classification", "暂无法判断"),
        "plain_text": (facts.get("pattern", {}) or {}).get("classification", "暂无法判断"),
        "evidence": list((facts.get("pattern", {}) or {}).get("evidence", [])),
    }
    projected["public_summary"] = facts_object.public_summary()
    profile = dict(projected.get("profile", {}) or {})
    profile["gender"] = "女" if facts_object.gender == "female" else "男"
    projected["profile"] = profile
    projected["facts"] = facts
    return projected


def _build_chart_signature_text_impl(chart: dict, prefix: str = "本盘差异依据") -> str:
    """生成一段可直接放进报告的差异化依据。"""
    facts = chart.get("facts")
    if isinstance(facts, dict):
        fp = build_chart_fingerprint(chart)
        strength = facts.get("strength", {}) or {}
        pillars = facts.get("pillars", []) or []
        elements = facts.get("element_counts", {}) or {}
        ten_gods = facts.get("ten_gods", {}) or {}
        pillar_names = ("年柱", "月柱", "日柱", "时柱")
        pillar_keys = ("year", "month", "day", "hour")
        structure: list[str] = []
        stem_signal = {
            "甲": "主动开拓与规划", "乙": "协作生长与细节", "丙": "表达行动与曝光", "丁": "专注表达与持续投入",
            "戊": "承接统筹与稳定", "己": "整理运营与落地", "庚": "执行规则与决断", "辛": "精修标准与边界",
            "壬": "资源流动与全局", "癸": "信息观察与适应",
        }
        branch_signal = {
            "子": "信息、安全感与流动", "丑": "积蓄、库存与耐心", "寅": "启动、学习与开拓", "卯": "合作、审美与关系",
            "辰": "资源库与复杂协调", "巳": "技术、热度与变化", "午": "表达、行动与影响", "未": "承接、家庭与细节",
            "申": "规则、技术与奔波", "酉": "标准、财务与精修", "戌": "责任、收尾与复盘", "亥": "人脉、远方与思路",
        }
        position_signal: list[str] = []
        for label, key, pillar in zip(pillar_names, pillar_keys, pillars):
            item = ten_gods.get(key, {}) if isinstance(ten_gods, dict) else {}
            hidden = "、".join(
                f"{value.get('gan', '')}{value.get('ten_god', '')}"
                for value in (item.get("hidden_stems", []) or [])
                if isinstance(value, dict)
            ) or "无"
            structure.append(
                f"{label}{pillar}：透干{item.get('gan', '未知')}，藏干{hidden}"
            )
            pillar_text = str(pillar)
            gan = pillar_text[:1]
            zhi = pillar_text[1:2]
            position_signal.append(
                f"{prefix}｜{label}{pillar_text}：天干侧重{stem_signal.get(gan, '阶段作用')}，"
                f"地支侧重{branch_signal.get(zhi, '现实承接')}。"
            )
        element_focus = {
            "木": "木的主轴偏向学习、生长、策划、教育与长期建设，现实判断要看计划能否持续落地。",
            "火": "火的主轴偏向表达、传播、技术热度、审美与行动，现实判断要看曝光能否转成稳定成果。",
            "土": "土的主轴偏向承接、运营、组织、空间与存量，现实判断要看资源是否形成稳定底盘。",
            "金": "金的主轴偏向规则、技术、合同、执行与精修，现实判断要看标准能否提高交付质量。",
            "水": "水的主轴偏向信息、沟通、贸易、流动与资源调度，现实判断要看变化中能否守住边界。",
        }
        ten_god_focus = {
            "比肩": "比肩突出时，重点是个人能力、同辈竞争和自主推进，合作前应先明确分工。",
            "劫财": "劫财突出时，重点是合作、人情和资源分配，账目、投入和退出规则需要前置。",
            "食神": "食神突出时，重点是稳定输出、产品、服务与口碑，适合把经验做成可复用成果。",
            "伤官": "伤官突出时，重点是创意、表达和技术突破，同时要处理好规则与沟通分寸。",
            "正财": "正财突出时，重点是稳定客户、预算、现金流与现实积累，收益需要可持续核算。",
            "偏财": "偏财突出时，重点是项目机会、商业判断与资源整合，每个机会都要核对成本。",
            "正官": "正官突出时，重点是责任、职位、流程与长期信用，适合用秩序承接目标。",
            "七杀": "七杀突出时，重点是竞争、目标压力与执行突破，需要同步建立风险控制。",
            "正印": "正印突出时，重点是学习、资质、系统和稳定支持，先补底层能力再扩大成果。",
            "偏印": "偏印突出时，重点是研究、策略、复盘和专业深化，想法需要通过小步验证落地。",
        }
        intro = (
            f"{prefix}：日主为{fp['day_master']}{fp['day_master_element']}，"
            f"强弱为{fp['strength']}；喜用{_join(fp['favorable_elements'], '暂需结合大运判断')}，"
            f"忌神{_join(fp['unfavorable_elements'], '暂不明显')}。"
        )
        detail_lines = [
            f"{prefix}｜四柱结构：{'；'.join(structure)}。",
            f"{prefix}｜五行权重：{'、'.join(f'{key}{float(value):.1f}' for key, value in sorted(elements.items()))}。",
            f"{prefix}｜强弱证据：{_join(strength.get('evidence', []), '证据待补')}。",
            f"{prefix}｜格局：{facts.get('pattern', {}).get('classification', '暂无法判断')}；证据：{_join(facts.get('pattern', {}).get('evidence', []), '证据待补')}。",
            (
                f"{prefix}｜十神分组：财星{fp['wealth_star_count']}、官杀{fp['officer_star_count']}、"
                f"食伤{fp['output_star_count']}、印星{fp['resource_star_count']}、比劫{fp['peer_star_count']}。"
            ),
            (
                f"{prefix}｜夫妻宫：{fp['day_branch']}{fp['spouse_palace_element']}，"
                f"藏干十神{_join(fp['spouse_palace_hidden_ten_gods'], '暂未读取')}。"
            ),
            f"{prefix}｜差异标签：{_join(fp.get('chart_summary_tags', []) + fp.get('career_pattern_tags', []) + fp.get('wealth_pattern_tags', []) + fp.get('love_pattern_tags', []))}。",
            f"{prefix}｜五行主轴：{element_focus.get(fp['top_elements'][0] if fp['top_elements'] else '', '五行主轴需结合结构继续观察')}",
            f"{prefix}｜十神主轴：{ten_god_focus.get(fp['top_ten_gods'][0] if fp['top_ten_gods'] else '', '十神主轴需结合结构继续观察')}",
            *position_signal,
        ]
        branch_order = "子丑寅卯辰巳午未申酉戌亥"
        month_branch = str(pillars[1])[1:2] if len(pillars) > 1 else ""
        offset = (
            (branch_order.find(month_branch) if month_branch in branch_order else 0)
            + ("甲乙丙丁戊己庚辛壬癸".find(fp["day_master"]) % len(detail_lines))
        ) % len(detail_lines)
        detail_lines = detail_lines[offset:] + detail_lines[:offset]
        return "\n".join([intro, *detail_lines])
    fp = build_chart_fingerprint(chart)
    strength = chart.get("day_master_strength", {})
    day_master = chart.get("day_master", "")
    day_element = STEM_ELEMENTS.get(day_master, "")
    favorable = _join(list(strength.get("favorable_elements", [])), "暂需结合大运判断")
    unfavorable = _join(list(strength.get("unfavorable_elements", [])), "暂不明显")
    tags = [
        *_join(fp.get("chart_summary_tags", [])).split("、"),
        *_join(fp.get("career_pattern_tags", [])).split("、"),
        *_join(fp.get("wealth_pattern_tags", [])).split("、"),
        *_join(fp.get("love_pattern_tags", [])).split("、"),
    ]
    unique_tags = []
    for tag in tags:
        if tag and tag not in unique_tags and tag != "暂不明显":
            unique_tags.append(tag)
    intro = (
        f"{prefix}：日主为{day_master}{day_element}，强弱为{strength.get('strength', '暂无法判断')}，净评分{float(strength.get('net_score', 0)):+.1f}；喜用{favorable}，忌神{unfavorable}。",
    )
    core_lines = [
        _profile_line(chart),
        _pillar_line(chart),
        _five_element_line(chart),
        _ten_god_line(chart),
        _day_master_profile(chart),
        _season_profile(chart),
        _group_profile(chart),
        _spouse_profile(chart),
        _strength_profile(chart),
        _pillar_story(chart),
        _gender_profile(chart),
        _top_ten_god_story(chart),
        _position_ten_god_story(chart),
        _event_focus_profile(chart),
        _element_event_profile(chart),
        _risk_action_profile(chart),
        _monthly_calibration_profile(chart),
        f"差异标签：{_join(unique_tags[:12])}。",
        _plain_tendency(chart),
    ]
    order_map = {
        "木": [4, 8, 11, 12, 13, 14, 15, 16, 5, 0, 1, 2, 3, 9, 10, 6, 7, 17, 18],
        "火": [4, 8, 11, 12, 13, 14, 15, 16, 5, 3, 6, 7, 10, 0, 1, 2, 9, 17, 18],
        "土": [4, 8, 11, 12, 13, 14, 15, 16, 2, 0, 1, 3, 7, 6, 10, 5, 9, 17, 18],
        "金": [4, 8, 11, 12, 13, 14, 15, 16, 3, 0, 1, 2, 7, 6, 10, 5, 9, 17, 18],
        "水": [4, 8, 11, 12, 13, 14, 15, 16, 2, 5, 6, 3, 0, 1, 10, 7, 9, 17, 18],
    }
    order = order_map.get(day_element, list(range(len(core_lines))))
    branch_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    month_zhi = chart.get("pillars", {}).get("month", {}).get("zhi", "")
    if month_zhi in branch_order and order:
        offset = branch_order.index(month_zhi) % len(order)
        order = order[offset:] + order[:offset]
    lines = [
        intro[0],
        *[f"{prefix}｜{core_lines[index]}" for index in order if index < len(core_lines)],
        f"{prefix}｜{_source_focus(chart)}",
    ]
    return "\n".join(lines)


def build_chart_signature_text(chart: dict, prefix: str = "本盘差异依据") -> str:
    """Render a report signature from the canonical ChartFacts projection."""
    if isinstance(chart.get("facts"), dict):
        projected = project_chart_facts_for_report(chart)
        projected.pop("facts", None)
        return _build_chart_signature_text_impl(projected, prefix)
    return _build_chart_signature_text_impl(chart, prefix)


def build_brief_signature(chart: dict) -> str:
    """生成较短的页面摘要，用于综合问盘等页面。"""
    fp = build_chart_fingerprint(chart)
    return (
        f"本盘重点：{fp.get('day_master', '')}{fp.get('day_master_element', '')}日主，"
        f"{fp.get('strength', '暂无法判断')}，喜用{_join(fp.get('favorable_elements', []))}，"
        f"忌神{_join(fp.get('unfavorable_elements', []))}；"
        f"事业看{_join(fp.get('career_pattern_tags', [])[:4])}，"
        f"财运看{_join(fp.get('wealth_pattern_tags', [])[:4])}，"
        f"关系看{_join(fp.get('love_pattern_tags', [])[:4])}。"
    )
