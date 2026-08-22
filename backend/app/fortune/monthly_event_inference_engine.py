# ruff: noqa  # Frozen compatibility port; protected by migration contracts.
"""
流月具体事件推断引擎 — v1.2-F

将流月从"泛事件标签"升级为按类型评分的大概率事件推断。
基于：流月十神、五行喜忌、地支关系、大运背景、原局特征。

来源：《渊海子平》《三命通会》《命理探源》
"""

from __future__ import annotations

from ..bazi.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from ..bazi.ten_gods import get_ten_god


# 事件类型定义
EVENT_TYPES = {
    "wealth_inflow": {"label": "项目进账/回款机会", "category": "财务"},
    "wealth_outflow": {"label": "人情支出/预算压力", "category": "财务"},
    "investment_risk": {"label": "投资谨慎/高风险机会", "category": "财务"},
    "cashflow_pressure": {"label": "现金流压力", "category": "财务"},
    "cooperation_money": {"label": "合伙分账/合作资金", "category": "财务"},
    "client_payment": {"label": "客户回款/订单收益", "category": "财务"},
    "business_surprise": {"label": "项目财务转机", "category": "财务"},
    "debt_loss": {"label": "破财漏财/借支担保", "category": "财务"},
    "social_drinking": {"label": "酒局人情/朋友应酬", "category": "人际往来"},
    "favor_obligation": {"label": "人情请托/朋友求助", "category": "人际往来"},
    "asset_purchase": {"label": "房车店铺/大件添置", "category": "房产居住"},
    "property_housing": {"label": "房子店铺/居住事务", "category": "房产居住"},
    "shop_property": {"label": "店铺门面/经营场地", "category": "房产居住"},
    "home_repair": {"label": "维修/改造/家庭设备", "category": "房产居住"},
    "family_asset": {"label": "家庭资产/田宅事务", "category": "房产居住"},
    "travel_traffic": {"label": "车辆出行/奔波变动", "category": "出行交通"},
    "travel_delay": {"label": "行程延误/临时变动", "category": "出行交通"},
    "vehicle_expense": {"label": "车辆维修/交通支出", "category": "出行交通"},
    "vehicle_safety": {"label": "车辆驾驶提醒", "category": "出行交通"},
    "safety_attention": {"label": "驾驶出行安全", "category": "出行交通"},
    "project_progress": {"label": "项目推进", "category": "事业工作"},
    "career_change": {"label": "岗位变化/工作调整", "category": "事业工作"},
    "boss_pressure": {"label": "上级压力/考核", "category": "事业工作"},
    "contract_document": {"label": "合同文书/文件审批", "category": "事业工作"},
    "legal_compliance": {"label": "规则合规/官非口舌", "category": "事业工作"},
    "official_dispute": {"label": "官非口舌/罚单投诉", "category": "事业工作"},
    "study_exam": {"label": "学习考试/证书培训", "category": "事业工作"},
    "public_expression": {"label": "汇报展示/作品发布", "category": "事业工作"},
    "relationship_progress": {"label": "感情推进/关系升温", "category": "感情关系"},
    "relationship_conflict": {"label": "关系摩擦/口舌误会", "category": "感情关系"},
    "old_contact": {"label": "旧人联系", "category": "感情关系"},
    "family_issue": {"label": "家庭事务/长辈事务", "category": "感情关系"},
    "cooperation": {"label": "合作/人际互动", "category": "事业工作"},
    "cooperation_boundary": {"label": "合作边界/朋友介入", "category": "感情关系"},
    "sleep_issue": {"label": "睡眠作息", "category": "健康状态"},
    "emotional_pressure": {"label": "情绪压力", "category": "健康状态"},
    "digestion_issue": {"label": "脾胃消化", "category": "健康状态"},
    "fire_anxiety": {"label": "心火焦虑", "category": "健康状态"},
    "kidney_fatigue": {"label": "腰肾疲劳", "category": "健康状态"},
    "respiratory_skin": {"label": "呼吸皮肤", "category": "健康状态"},
    "health_fluctuation": {"label": "身体状态提醒", "category": "健康状态"},
    "medical_attention": {"label": "身体检查/小病早看", "category": "健康状态"},
    "illness_symbol_attention": {"label": "病符小疾/体检复查", "category": "健康状态"},
    "overwork": {"label": "过劳提醒", "category": "健康状态"},
}

SOURCE_IDS = ["yuan_hai_zi_ping", "san_ming_tong_hui", "ming_li_tan_yuan"]
EXTENDED_SOURCE_IDS = SOURCE_IDS + ["yu_zhao_ding_zhen_jing", "wu_xing_jing_ji"]
SOURCE_TITLES = {
    "yuan_hai_zi_ping": "《渊海子平》",
    "san_ming_tong_hui": "《三命通会》",
    "ming_li_tan_yuan": "《命理探源》",
    "yu_zhao_ding_zhen_jing": "《玉照定真经》",
    "wu_xing_jing_ji": "《五行精纪》",
    "xing_ping_hui_hai": "《星平会海》",
    "xie_ji_bian_fang_shu": "《协纪辨方书》",
}

EVENT_PLAIN_DETAILS = {
    "wealth_inflow": {
        "plain_summary": "本月更像是项目款、客户回款或副业进账被点亮。",
        "real_world_signals": ["客户回款", "项目结算", "副业进账", "资源变现"],
        "basis": "财星、食伤或喜用五行被流月带动时，现实中常落到订单、回款和收益确认。",
    },
    "wealth_outflow": {
        "plain_summary": "本月更像是人情、饭局、设备或临时事项带来花费。",
        "real_world_signals": ["饭局人情", "朋友求助", "设备采购", "预算超支"],
        "basis": "比劫、忌神和冲动叠加时，财务上容易表现为分账、人情和计划外支出。",
    },
    "business_surprise": {
        "plain_summary": "本月项目或财务上可能出现转机，适合盯紧机会但先算清成本。",
        "real_world_signals": ["项目突破", "回款转机", "报价谈判", "临时机会"],
        "basis": "财星遇喜用或食伤生财时，容易从项目、客户和资源流转中看到进展。",
    },
    "client_payment": {
        "plain_summary": "本月更适合盯客户回款、订单确认、账期推进和项目尾款。",
        "real_world_signals": ["客户回款", "订单确认", "尾款结算", "报价落地"],
        "basis": "财星、食伤生财和喜用五行叠加时，现实中更容易落到客户、订单和款项确认。",
    },
    "debt_loss": {
        "plain_summary": "本月要防人情借支、冲动消费、替人垫款或分账不清带来的破财感。",
        "real_world_signals": ["朋友借钱", "替人垫款", "合伙分账", "计划外支出"],
        "basis": "比劫制财、财星为忌或冲动叠加时，财务压力常从人情、分账和临时支出显现。",
    },
    "social_drinking": {
        "plain_summary": "本月人情局、饭局酒局或朋友邀约会变多，边界比热闹更重要。",
        "real_world_signals": ["酒局饭局", "朋友邀约", "人情开销", "口头承诺"],
        "basis": "比劫、桃花地支或冲日支被引动时，人际往来容易变密，需注意口舌和分寸。",
    },
    "favor_obligation": {
        "plain_summary": "本月容易遇到朋友求助、人情请托或需要帮忙协调的事。",
        "real_world_signals": ["朋友求助", "人情请托", "帮人协调", "口头承诺"],
        "basis": "比劫和劫财代表同辈、人情和资源分配，遇冲或财星受压时，容易变成现实消耗。",
    },
    "asset_purchase": {
        "plain_summary": "本月容易动到房子、车子、店铺、装修或大件添置的念头。",
        "real_world_signals": ["看房看车", "店铺设备", "装修维修", "大件采购"],
        "basis": "财星、土象、印星和居住宫位被引动时，现实中常落到资产、房店和设备。",
    },
    "property_housing": {
        "plain_summary": "本月房子、店铺、居住环境或家庭资产类事情更容易被推到台前。",
        "real_world_signals": ["房子店铺", "搬家装修", "租约调整", "家庭资产"],
        "basis": "土象、印星、财星或日支被冲动时，容易对应房产、居住和家庭承载事务。",
    },
    "shop_property": {
        "plain_summary": "本月店铺、门面、办公室、经营场地或设备添置类事情更值得关注。",
        "real_world_signals": ["店铺门面", "办公室场地", "经营设备", "租约成本"],
        "basis": "土象主场地承载，财星主经营流转，印星主固定资源，三者叠加时容易落到店铺和经营空间。",
    },
    "travel_traffic": {
        "plain_summary": "本月更像是车辆、通勤、差旅或临时奔波被点亮。",
        "real_world_signals": ["车辆出行", "通勤奔波", "临时跑动", "路线变动"],
        "basis": "年支、时支或驿动象被冲动时，现实中常表现为外出、车辆和奔波增加。",
    },
    "vehicle_expense": {
        "plain_summary": "本月车辆、交通工具或出行成本需要多留预算。",
        "real_world_signals": ["车辆保养", "维修支出", "油费停车", "交通罚单谨慎"],
        "basis": "冲动出行位且财星或忌神参与时，容易从车辆和交通成本上体现。",
    },
    "vehicle_safety": {
        "plain_summary": "本月开车、骑行或赶路时更需要慢一点、稳一点。",
        "real_world_signals": ["开车谨慎", "避免疲劳驾驶", "检查车况", "行程留缓冲"],
        "basis": "七杀、冲动和忌神叠加时，适合把风险转化为车辆检查和行程管理。",
    },
    "safety_attention": {
        "plain_summary": "本月出行和工具使用要多留心，适合提前排查小隐患。",
        "real_world_signals": ["驾驶安全", "工具设备", "赶时间风险", "临时变动"],
        "basis": "冲动、七杀或火金失衡时，现实提醒应落在安全习惯和风险预防上。",
    },
    "contract_document": {
        "plain_summary": "本月文件、合同、审批和流程确认会更重要。",
        "real_world_signals": ["合同条款", "审批流程", "资料补充", "书面确认"],
        "basis": "官杀、伤官和月支工作位被引动时，现实中常落到规则、文件和流程。",
    },
    "official_dispute": {
        "plain_summary": "本月要注意规则、投诉、罚单、口舌争执或流程合规类问题。",
        "real_world_signals": ["规则合规", "投诉争执", "罚单提醒", "流程瑕疵"],
        "basis": "官杀代表规则压力，伤官代表表达突破，七杀遇冲或金象规则明显时，容易出现口舌与合规提醒。",
    },
    "relationship_progress": {
        "plain_summary": "本月关系沟通有推进空间，适合把话说清楚、把节奏放稳。",
        "real_world_signals": ["确认关系", "约见沟通", "合作推进", "关系升温"],
        "basis": "财官、桃花或日支关系位遇喜用时，关系层面更容易出现推进信号。",
    },
    "relationship_conflict": {
        "plain_summary": "本月关系里容易因语气、边界或旧问题出现摩擦。",
        "real_world_signals": ["伴侣沟通", "合作边界", "旧事重提", "口舌误会"],
        "basis": "日支、比劫、伤官或忌神被冲动时，关系压力容易通过表达和边界显现。",
    },
    "family_issue": {
        "plain_summary": "本月家庭、长辈、房屋或旧事务可能需要你分心处理。",
        "real_world_signals": ["长辈事务", "家庭沟通", "旧事重提", "家中安排"],
        "basis": "年支对应家庭背景和长辈环境，印星和土象也主承载与居住，被流月引动时容易落到家庭事务。",
    },
    "health_fluctuation": {
        "plain_summary": "本月身体状态容易被压力、作息或情绪牵动，宜早休息、早处理小问题。",
        "real_world_signals": ["身体疲劳", "睡眠作息", "情绪压力", "小病早看"],
        "basis": "忌神、官杀压力或冲动叠加时，应转化为作息、体检和身体信号管理。",
    },
    "medical_attention": {
        "plain_summary": "本月适合留意身体给出的早期信号，小不适不要拖。",
        "real_world_signals": ["复查体检", "炎症上火", "肠胃睡眠", "按时休息"],
        "basis": "病符类取象、五行偏枯和流月压力叠加时，只做健康管理提醒，不做医学诊断。",
    },
    "illness_symbol_attention": {
        "plain_summary": "本月有病符小疾类提醒，适合早睡、复查、体检或把小问题及时处理。",
        "real_world_signals": ["小病早看", "复查体检", "炎症上火", "疲劳积累"],
        "basis": "官杀压力、忌神、冲动和五行偏枯叠加时，传统取象会转成身体管理提醒，不作医学诊断。",
    },
}

# 用于概率等级描述
_PROB_HIGH = "较高"
_PROB_MED = "中等"
_PROB_LOW = "需观察"


REALITY_EVENT_RULES = {
    "vehicle_safety": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "七杀或压力星被引动",
            "年支或时支被冲动",
            "火金工具象明显",
            "忌神参与",
            "流月主事件池命中",
        ],
    },
    "property_housing": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "土象被引动",
            "印星或财星参与",
            "日支居住位被冲",
            "喜用五行助力",
            "流月主事件池命中",
        ],
    },
    "shop_property": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "财星带动经营",
            "土象场地事务",
            "印星承载资产",
            "项目或客户信号出现",
            "流月主事件池命中",
        ],
    },
    "contract_document": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "官杀规则星被引动",
            "伤官表达与规则相遇",
            "月支工作位被冲",
            "金象文书规则明显",
            "流月主事件池命中",
        ],
    },
    "illness_symbol_attention": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "忌神压身",
            "官杀压力较重",
            "冲动身体状态",
            "五行偏枯或火土金压力",
            "流月主事件池命中",
        ],
    },
    "social_drinking": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "比劫朋友星被引动",
            "桃花地支带来应酬",
            "忌神带来人情消耗",
            "日支被冲易口舌",
            "流月主事件池命中",
        ],
    },
    "favor_obligation": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "比劫或劫财明显",
            "朋友同辈求助",
            "财星被消耗",
            "关系位被冲",
            "流月主事件池命中",
        ],
    },
    "official_dispute": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "官杀规则压力",
            "伤官见官",
            "七杀遇冲",
            "金象规则或罚单信号",
            "流月主事件池命中",
        ],
    },
    "debt_loss": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "比劫制财",
            "财星为忌",
            "冲动带来计划外支出",
            "偏财过重",
            "流月主事件池命中",
        ],
    },
    "client_payment": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "正财或偏财被引动",
            "食伤生财",
            "喜用五行助力",
            "年度喜用相关",
            "流月主事件池命中",
        ],
    },
    "relationship_progress": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "财官关系星被引动",
            "子午卯酉桃花地支",
            "日支关系位被触发",
            "喜用五行助力",
            "流月主事件池命中",
        ],
    },
    "family_issue": {
        "min_trigger_count": 2,
        "trigger_conditions": [
            "年支家庭位被冲",
            "印星或土象家庭承载",
            "房产田宅信号出现",
            "长辈或旧事被引动",
            "流月主事件池命中",
        ],
    },
}


def _is_favorable(element: str, favorable_elements: list[str]) -> bool:
    return element in favorable_elements


def _is_unfavorable(element: str, unfavorable_elements: list[str]) -> bool:
    return element in unfavorable_elements


def _score_event(base: float, conditions: list[bool], weights: list[float] = None) -> float:
    """根据多个条件打分，返回 0-100 之间的分数。"""
    if weights is None:
        weights = [1.0] * len(conditions)
    score = base
    for cond, w in zip(conditions, weights):
        if cond:
            score += w * 15
    return min(100, max(0, score))


def infer_monthly_likely_events(
    chart: dict,
    monthly_item: dict,
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> dict:
    """
    推断该月的大概率事件列表。
    返回 Top 3-5 事件。
    """
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = strength.get("favorable_elements", []) or []
    unfavorable = strength.get("unfavorable_elements", []) or []
    ten_god_counts = chart.get("ten_god_counts", {}) or {}

    gan = monthly_item.get("gan", "")
    zhi = monthly_item.get("zhi", "")
    ten_god = monthly_item.get("ten_god", get_ten_god(day_master, gan) if gan else "")
    gan_element = STEM_ELEMENTS.get(gan, "")
    zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")

    # 地支关系
    from ..bazi.branch_relations import analyze_year_branch_relations

    branch_rels = monthly_item.get("branch_relations", analyze_year_branch_relations(chart, zhi))
    has_clash = monthly_item.get(
        "has_clash",
        any(r.get("relation_type") == "六冲" for r in branch_rels) if branch_rels else False,
    )

    # 构建事件评分
    event_scores = {}

    # ---- 财务类 ----
    is_cai = ten_god in ("正财", "偏财")
    is_shishen = ten_god in ("食神", "伤官")
    is_bi_jie = ten_god in ("比肩", "劫财")

    # 财运进入
    conditions = [
        is_cai,
        _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable),
        is_shishen,
        yearly_data is not None and yearly_data.get("relation_to_favorable") == "喜用相关",
        is_cai and not has_clash,
    ]
    event_scores["wealth_inflow"] = _score_event(20, conditions, [1.5, 1.5, 1.2, 1.2, 1.0])

    # 支出破财
    conditions = [
        is_cai and _is_unfavorable(gan_element, unfavorable),
        is_bi_jie,
        has_clash and _is_unfavorable(zhi_element, unfavorable),
        ten_god_counts.get("偏财", 0) > ten_god_counts.get("正财", 0) + 1
        if ten_god_counts
        else False,
        is_bi_jie and has_clash,
    ]
    event_scores["wealth_outflow"] = _score_event(15, conditions, [1.5, 1.5, 1.5, 1.0, 1.5])

    # 房产居住
    is_tu = zhi_element == "土" or gan_element == "土"
    is_yin = ten_god in ("偏印", "正印")
    is_cai_yin = ten_god in ("正财", "偏财", "正印", "偏印")
    has_year_clash = has_clash and zhi == chart.get("pillars", {}).get("year", {}).get("zhi", "")
    has_day_clash = has_clash and zhi == chart.get("pillars", {}).get("day", {}).get("zhi", "")
    conditions = [
        is_tu,
        is_yin and _is_favorable(gan_element, favorable),
        is_cai_yin and _is_favorable(zhi_element, favorable),
        has_year_clash or has_day_clash,
        is_tu and has_clash,
    ]
    event_scores["property_housing"] = _score_event(20, conditions, [1.5, 1.5, 1.2, 1.5, 1.5])

    # 出行交通
    has_year_clash = has_clash and zhi == chart.get("pillars", {}).get("year", {}).get("zhi", "")
    has_hour_clash = has_clash and zhi == chart.get("pillars", {}).get("hour", {}).get("zhi", "")
    has_day_clash = has_clash and zhi == chart.get("pillars", {}).get("day", {}).get("zhi", "")
    is_water_fire = gan_element in ("水", "火") or zhi_element in ("水", "火")
    conditions = [
        has_year_clash or has_hour_clash or has_day_clash,
        has_clash
        and _is_unfavorable(gan_element, unfavorable)
        and _is_unfavorable(zhi_element, unfavorable),
        ten_god in ("偏财", "七杀"),
        has_clash and is_water_fire,
        has_clash,
    ]
    event_scores["travel_traffic"] = _score_event(20, conditions, [1.5, 1.5, 1.2, 1.2, 1.0])

    # 合同文书/官非
    is_guan = ten_god in ("正官", "七杀")
    is_shang = ten_god == "伤官"
    conditions = [
        is_guan and _is_unfavorable(gan_element, unfavorable),
        is_shang and is_guan,
        has_clash and zhi == chart.get("pillars", {}).get("month", {}).get("zhi", ""),
        is_guan,
    ]
    event_scores["contract_document"] = _score_event(20, conditions, [1.5, 1.5, 1.5, 1.0])

    # 感情推进
    is_cai_guan = ten_god in ("正财", "偏财", "正官", "七杀")
    is_peach = zhi in ("子", "午", "卯", "酉") and _is_favorable(zhi_element, favorable)
    conditions = [
        is_cai_guan and _is_favorable(gan_element, favorable),
        is_peach,
        yearly_data is not None and yearly_data.get("relation_to_favorable") == "喜用相关",
        zhi in ("子", "午", "卯", "酉"),
    ]
    event_scores["relationship_progress"] = _score_event(15, conditions, [1.5, 1.5, 1.2, 1.0])

    # 感情摩擦
    conditions = [
        has_clash and (zhi == chart.get("pillars", {}).get("day", {}).get("zhi", "")),
        is_bi_jie and ten_god_counts.get("劫财", 0) > 1,
        is_shang and ten_god_counts.get("伤官", 0) > 1,
        has_clash and _is_unfavorable(zhi_element, unfavorable),
    ]
    event_scores["relationship_conflict"] = _score_event(15, conditions, [1.5, 1.5, 1.5, 1.2])

    # 健康波动
    over_weak = any(_is_unfavorable(e, unfavorable) for e in [gan_element, zhi_element])
    is_guan_sha = ten_god in ("正官", "七杀")
    conditions = [
        over_weak,
        is_guan_sha and _is_unfavorable(gan_element, unfavorable),
        has_clash and _is_unfavorable(zhi_element, unfavorable),
        has_clash,
    ]
    event_scores["health_fluctuation"] = _score_event(15, conditions, [1.5, 1.5, 1.5, 1.0])

    # 事业变化
    is_guan_yin = ten_god in ("正官", "七杀", "正印", "偏印")
    conditions = [
        is_guan_yin and has_clash,
        yearly_data is not None and _is_favorable(yearly_data.get("gan_element", ""), favorable),
        is_guan_yin and _is_unfavorable(gan_element, unfavorable),
    ]
    event_scores["career_change"] = _score_event(15, conditions, [1.5, 1.5, 1.2])

    # 学习考试
    is_yin_shou = ten_god in ("正印", "偏印")
    conditions = [
        is_yin_shou and _is_favorable(gan_element, favorable),
        yearly_data is not None and yearly_data.get("relation_to_favorable") == "喜用相关",
        is_yin_shou,
    ]
    event_scores["study_exam"] = _score_event(20, conditions, [1.5, 1.2, 1.0])

    # 合作
    is_bi = ten_god in ("比肩", "劫财")
    conditions = [
        is_bi and has_clash,
        is_bi and _is_favorable(gan_element, favorable),
        is_bi,
    ]
    event_scores["cooperation"] = _score_event(15, conditions, [1.5, 1.2, 1.0])

    # 筛选 Top 事件
    sorted_events = sorted(event_scores.items(), key=lambda x: -x[1])
    top_events = []
    for event_type, score in sorted_events:
        if score >= 22 and len(top_events) < 5:
            evt_info = EVENT_TYPES.get(event_type, {"label": event_type, "category": "其他"})
            probability_level = (
                _PROB_HIGH if score >= 60 else _PROB_MED if score >= 40 else _PROB_LOW
            )
            top_events.append(
                {
                    "event_type": event_type,
                    "label": evt_info["label"],
                    "category": evt_info["category"],
                    "probability_level": probability_level,
                    "score": round(score, 1),
                    "reason": _generate_reason(
                        event_type, ten_god, gan_element, zhi_element, has_clash, zhi
                    ),
                    "advice": _generate_advice(event_type),
                    "source_ids": SOURCE_IDS,
                }
            )

    # 如果没有达到 2 条低分事件，补充基础事件
    if len(top_events) < 2:
        base_events = _get_base_events(ten_god, gan_element, zhi_element)
        for be in base_events:
            if be["event_type"] not in [e["event_type"] for e in top_events]:
                top_events.append(be)
            if len(top_events) >= 2:
                break

    # 分离警告和机会
    event_warnings = [e for e in top_events if e["score"] >= 50 and "风险" in e.get("advice", "")]
    event_opportunities = [
        e for e in top_events if e["score"] >= 50 and "风险" not in e.get("advice", "")
    ]

    source_titles = ["《渊海子平》", "《三命通会》", "《命理探源》"]

    return {
        "event_score_map": {k: round(v, 1) for k, v in sorted_events},
        "top_events": top_events[:5],
        "event_warnings": event_warnings[:3],
        "event_opportunities": event_opportunities[:3],
        "basis": f"流月十神为{ten_god}，天干{gan}({gan_element})，地支{zhi}({zhi_element})，"
        f"五行喜忌关系综合分析。{'地支存在六冲关系，容易激发该宫位对应事务。' if has_clash else ''}",
        "source_titles": source_titles,
    }


def _generate_reason(
    event_type: str,
    ten_god: str,
    gan_element: str,
    zhi_element: str,
    has_clash: bool,
    zhi: str = "",
) -> str:
    """生成事件触发原因（含具体干支五行）。"""
    clash_note = f"，且地支存在相冲关系易激发对应宫位事务" if has_clash else ""
    reasons = {
        "wealth_inflow": f"流月十神为{ten_god}，天干{gan_element}五行，财星被引动{clash_note}，适合关注客户回款、项目收益或副业收入。",
        "wealth_outflow": f"流月{ten_god}引动，{gan_element}{zhi_element}五行{'忌神' if not None else ''}层面支出压力较容易被触发{clash_note}，建议提前规划预算。",
        "client_payment": f"流月十神为{ten_god}，财星或食伤生财信号被引动{clash_note}，适合关注客户回款、订单确认和项目尾款。",
        "debt_loss": f"流月{ten_god}引动比劫或财务消耗信号{clash_note}，人情借支、分账不清和计划外支出需要多留心。",
        "property_housing": f"流月{zhi_element}象或{ten_god}被引动{clash_note}，容易涉及房产、居住、装修、搬迁或家庭资产类事务，现实中若有相关计划本月更容易推进。",
        "shop_property": f"流月{zhi_element}象和{ten_god}共同引动经营承载事务{clash_note}，店铺门面、办公室场地、租约和设备添置需要重点看成本。",
        "travel_traffic": f"流月{zhi}地支冲动年/日/时支{clash_note}，出行、通勤、差旅节奏容易增加，驾车和长途行程建议提前规划。",
        "vehicle_safety": f"流月{ten_god}带压力星信号，{gan_element}{zhi_element}五行又见工具与冲动象{clash_note}，车辆驾驶、骑行和赶路需要放慢节奏。",
        "contract_document": f"流月十神为{ten_god}，官杀或文书规则被引动{clash_note}，合同、审批、流程、制度类事务需重点留意，重要事项建议落到文字。",
        "official_dispute": f"流月{ten_god}引动规则压力、口舌或合规信号{clash_note}，投诉、罚单、制度流程和表达分寸需要提前管控。",
        "relationship_progress": f"流月财星或官星（{ten_god}）被引动{clash_note}，感情或人际关系推进信号较明显，适合主动沟通。",
        "relationship_conflict": f"流月冲动日支配偶宫（{zhi}）{clash_note}，亲密关系或合作关系容易出现节奏不一致或表达误会。",
        "family_issue": f"流月{zhi}引动家庭、长辈、居住或旧事务信号{clash_note}，家中安排和长辈沟通可能需要分心处理。",
        "health_fluctuation": f"流月{ten_god}为忌神，{gan_element}{zhi_element}五行加重原局压力{clash_note}，健康方面容易出现作息、情绪或某五行对应的身体状态波动。",
        "illness_symbol_attention": f"流月{ten_god}带来压力或忌神信号，{gan_element}{zhi_element}五行叠加冲动{clash_note}，适合把小不适转成复查、体检和作息管理。",
        "favor_obligation": f"流月{ten_god}引动朋友同辈、人情往来和资源分配{clash_note}，容易遇到请托、求助或口头承诺。",
        "career_change": f"流月{ten_god}引动，官杀印星相关事务被激活{clash_note}，事业或岗位调整机会较容易出现。",
        "study_exam": f"流月{ten_god}（印星）被引动{clash_note}，学习考试效率较高，适合集中精力备考或完成书面工作。",
        "cooperation": f"流月{ten_god}（比劫）被引动{clash_note}，合作邀约、人际互动或团队协调机会增多。",
    }
    base_reason = reasons.get(
        event_type,
        f"流月{ten_god}和{gan_element}{zhi_element}五行被引动{clash_note}，相关事务容易被触发。",
    )
    return base_reason


def _generate_advice(event_type: str) -> str:
    """生成行动建议（含现实处理方案）。"""
    advices = {
        "wealth_inflow": "把客户、项目、副业和回款逐项列清，机会来了先核对交付、成本和到账时间。",
        "wealth_outflow": "饭局人情、朋友借支、设备采购和冲动消费都先设预算，超过预算就暂缓。",
        "client_payment": "把客户、订单、账期和尾款逐项核对，能书面确认的尽量落到文字。",
        "debt_loss": "涉及借钱、垫款、担保和合伙分账先暂停一下，把金额、期限和责任写清楚。",
        "business_surprise": "遇到项目或财务转机时，先核实合同、成本和责任人，再决定是否加码。",
        "social_drinking": "饭局酒局可以参加，但少替人担保、少做口头承诺，开车时避免饮酒和疲劳。",
        "favor_obligation": "帮忙可以量力而行，先说明能帮到哪里、不能承担什么，避免人情变成压力。",
        "asset_purchase": "看房、看车、看店铺可以推进调研，真正付款前要复核现金流和长期成本。",
        "property_housing": "房子、店铺、装修和租约可以提前看方案，重大付款要结合现实预算和合同。",
        "shop_property": "看门面、办公室、设备和租约时，先算固定成本、押金、回本周期和退出条件。",
        "travel_traffic": "提前检查路线、车况和时间余量，临时行程尽量少赶路、少冒进。",
        "vehicle_expense": "车辆保养、维修、停车、保险和罚单风险都预留一点预算，别等到临时处理。",
        "vehicle_safety": "开车、骑行、长途和夜间出行都放慢节奏，先检查车况，避免疲劳驾驶。",
        "safety_attention": "工具、车辆、路程和临时变动都多检查一遍，把小隐患处理在前面。",
        "contract_document": "合同、审批、报价和流程都落到文字，金额、时间、责任边界逐条确认。",
        "official_dispute": "涉及投诉、罚单、合同争议和制度流程时，先留证据、少口头争辩，必要时咨询专业人士。",
        "relationship_conflict": "本月亲密关系或合作关系容易出现节奏不一致或误会，建议少用情绪推动决定，沟通时多确认对方真实意图。",
        "relationship_progress": "适合把关系、合作和长期安排说清楚，但节奏宜稳，不宜用压力推进。",
        "health_fluctuation": "把睡眠、饮食、运动和压力先稳住；身体有信号时及时休息或做现实检查。",
        "medical_attention": "小不适不拖延，适合安排体检、复查或调整作息；身体问题以医生意见为准。",
        "illness_symbol_attention": "把小病小痛当提醒，适合早睡、复查、体检或调整作息；身体问题以医生意见为准。",
        "career_change": "本月适合评估当前岗位方向，但重要跳槽决策建议留到更多信息确认后再做；短期调整可积极推进。",
        "study_exam": "本月适合安排学习计划、考试备考、证书培训，容易事半功倍；适合集中精力完成书面或知识类工作。",
        "cooperation": "本月合作邀约或人际互动增多，适合推进合作沟通，但重大协议和资金安排需留足核实周期。",
    }
    return advices.get(
        event_type, "建议结合现实情况灵活应对，重要决策留出核实和确认时间，不因命理提示而冲动行事。"
    )


def _source_titles(source_ids: list[str]) -> list[str]:
    """把来源 id 转成中文书名。"""
    return [SOURCE_TITLES.get(sid, sid) for sid in source_ids]


def _complete_trigger_factors(
    factors: list[str],
    ten_god: str = "",
    gan_element: str = "",
    zhi_element: str = "",
    has_clash: bool = False,
) -> list[str]:
    """保证事件至少有两条用户可理解的触发依据。"""
    result = [str(item) for item in factors if item]
    if ten_god and not any("十神" in item for item in result):
        result.append(f"流月十神为{ten_god}")
    if gan_element or zhi_element:
        result.append(f"流月五行为{gan_element or '未知'}{zhi_element or ''}")
    if has_clash:
        result.append("地支冲动带来变动")
    if len(result) < 2:
        result.append("月度事件池匹配")
    return list(dict.fromkeys(result))[:8]


def _enrich_event_payload(
    event: dict,
    ten_god: str = "",
    gan_element: str = "",
    zhi_element: str = "",
    has_clash: bool = False,
) -> dict:
    """补充普通用户能看懂的事件对象、依据和来源。"""
    event_type = event.get("event_type", "")
    detail = EVENT_PLAIN_DETAILS.get(event_type, {})
    info = EVENT_TYPES.get(event_type, {})
    source_ids = detail.get("source_ids") or event.get("source_ids") or EXTENDED_SOURCE_IDS
    event["label"] = info.get("label", event.get("label", event_type))
    event["plain_summary"] = event.get("plain_summary") or detail.get(
        "plain_summary",
        f"本月更容易出现和{event.get('label', '现实事务')}相关的信号。",
    )
    event["real_world_signals"] = event.get("real_world_signals") or detail.get(
        "real_world_signals", ["现实计划", "沟通确认", "预算安排"]
    )
    event["basis"] = event.get("basis") or detail.get(
        "basis", "根据流月十神、五行喜忌和地支关系做趋势参考。"
    )
    event["source_ids"] = source_ids
    event["source_titles"] = event.get("source_titles") or _source_titles(source_ids)
    event["trigger_factors"] = _complete_trigger_factors(
        event.get("trigger_factors", []),
        ten_god=ten_god,
        gan_element=gan_element,
        zhi_element=zhi_element,
        has_clash=has_clash,
    )
    # v1.3-A2: 变体选择
    event["evidence"] = event.get("trigger_factors", [])[:]
    event["trigger_count"] = len(event.get("trigger_factors", []))
    event = _apply_variant_to_event(event, event.get("trigger_factors", []))
    return event


def _get_base_events(ten_god: str, gan_element: str, zhi_element: str) -> list[dict]:
    """生成基础保底事件。"""
    base = []
    if "财" in ten_god:
        base.append(
            {
                "event_type": "wealth_inflow",
                "label": "财运进入/收入机会",
                "category": "财务",
                "probability_level": "需观察",
                "score": 20.0,
                "reason": "流月财星显现，财务机会存在被引动可能。",
                "advice": "建议保持关注，但不宜仅凭命理信息做重大财务决定。",
                "source_ids": ["yuan_hai_zi_ping"],
            }
        )
    if "官" in ten_god or "杀" in ten_god:
        base.append(
            {
                "event_type": "contract_document",
                "label": "合同文书/文件审批",
                "category": "事业工作",
                "probability_level": "需观察",
                "score": 20.0,
                "reason": "流月官杀显现，规则、合同、审批类事务需重点留意。",
                "advice": "建议重要事项落到文字、确认流程细节。",
                "source_ids": ["yuan_hai_zi_ping"],
            }
        )
    if "印" in ten_god:
        base.append(
            {
                "event_type": "study_exam",
                "label": "学习考试/证书培训",
                "category": "事业工作",
                "probability_level": "需观察",
                "score": 20.0,
                "reason": "流月印星显现，学习效率较高，适合安排考级、培训、进修类事务。",
                "advice": "适合制定学习计划，有助于知识技能积累。",
                "source_ids": ["yuan_hai_zi_ping"],
            }
        )
    return base


# ====== v1.2-F-Fix: 增强函数 ======


def _identify_clash_influence_area(zhi: str, chart: dict) -> dict:
    """识别流月地支冲击的目标宫位，返回具体影响领域。"""
    pillars = chart.get("pillars", {})
    year_zhi = pillars.get("year", {}).get("zhi", "")
    month_zhi = pillars.get("month", {}).get("zhi", "")
    day_zhi = pillars.get("day", {}).get("zhi", "")
    hour_zhi = pillars.get("hour", {}).get("zhi", "")

    clashes = []
    if zhi == year_zhi:
        clashes.append(
            {
                "_type": "年支",
                "_label": "家庭/长辈/外部环境",
                "_events": ["family_issue", "old_contact", "travel_traffic", "public_expression"],
            }
        )
    if zhi == month_zhi:
        clashes.append(
            {
                "_type": "月支",
                "_label": "工作/职场/流程/上级",
                "_events": [
                    "contract_document",
                    "boss_pressure",
                    "career_change",
                    "project_progress",
                ],
            }
        )
    if zhi == day_zhi:
        clashes.append(
            {
                "_type": "日支",
                "_label": "伴侣/关系/居住/自我",
                "_events": [
                    "relationship_conflict",
                    "relationship_progress",
                    "property_housing",
                    "sleep_issue",
                ],
            }
        )
    if zhi == hour_zhi:
        clashes.append(
            {
                "_type": "时支",
                "_label": "出行/长期规划/子女/副业",
                "_events": ["travel_traffic", "career_change", "old_contact", "study_exam"],
            }
        )
    return {"clashes": clashes, "has_clash": len(clashes) > 0}


def _get_clash_driven_events(
    zhi: str,
    chart: dict,
    ten_god: str,
    gan_element: str,
    zhi_element: str,
    favorable: list,
    unfavorable: list,
) -> list[dict]:
    """根据地支冲击目标生成差异化事件及加分。"""
    info = _identify_clash_influence_area(zhi, chart)
    events = []
    for c in info.get("clashes", []):
        for etype in c["_events"]:
            evt_info = EVENT_TYPES.get(etype, {"label": etype, "category": "其他"})
            base_score = 30
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                base_score += 15
            if _is_favorable(gan_element, favorable) and _is_favorable(zhi_element, favorable):
                base_score += 10
            reason_map = {
                "family_issue": f"流月{zhi}地支冲年支，家庭、长辈或外部环境事务较容易被引动{c['_label']}，原有家庭事务可能需要调整或重新确认。",
                "old_contact": f"流月{zhi}地支冲年/时支，旧关系、旧项目或旧思路可能重新出现{c['_label']}，适合复盘但不建议全盘否定现有方向。",
                "travel_traffic": f"流月{zhi}地支冲年/时支{c['_label']}，出行、差旅、通勤或奔波节奏较容易增加，长途行程建议提前规划。",
                "contract_document": f"流月{zhi}地支冲月支{c['_label']}，工作流程、合同审批、制度规范类事务需要重点确认，重要事项建议落到文字。",
                "boss_pressure": f"流月{zhi}地支冲月支{c['_label']}，上级要求、考核或职场规则压力容易被触发，适合提前沟通预期。",
                "career_change": f"流月{zhi}地支冲月/时支{c['_label']}，事业方向、岗位或长期规划可能需要重新评估。",
                "relationship_conflict": f"流月{zhi}地支冲日支配偶宫{c['_label']}，亲密关系或合作伙伴容易出现节奏不一致或表达误会，建议少用情绪推动决定。",
                "relationship_progress": f"流月{zhi}地支冲日支{c['_label']}，关系领域被触发，有利有弊——旧问题可能被翻出，但也适合重新确认关系定位。",
                "property_housing": f"流月{zhi}地支冲日支{c['_label']}，居住、搬迁、装修或家庭资产类事务容易被动推动。",
                "study_exam": f"流月{zhi}地支冲时支{c['_label']}，长期计划或学习安排可能需要调整，适合重新做规划。",
            }
            events.append(
                {
                    "event_type": etype,
                    "label": evt_info["label"],
                    "category": evt_info["category"],
                    "probability_level": "中等" if base_score >= 40 else "需观察",
                    "score": base_score,
                    "reason": reason_map.get(
                        etype, f"流月{zhi}地支{c['_type']}被冲{c['_label']}，相关事务容易被触发"
                    ),
                    "advice": _generate_advice(etype),
                    "trigger_factors": [f"地支冲击{c['_type']}_{c['_label']}"],
                    "source_ids": SOURCE_IDS,
                }
            )
    return events


def _get_season_events(
    month_num: int, gan_element: str, zhi_element: str, favorable: list
) -> list[dict]:
    """基于月份季节生成季节事件加分。"""
    season_map = {
        "spring": {
            "months": [1, 2, 3],
            "elements": ["木"],
            "label": "春季·生发",
            "events": [("study_exam", 15), ("project_progress", 15), ("public_expression", 10)],
        },
        "summer": {
            "months": [4, 5, 6],
            "elements": ["火"],
            "label": "夏季·旺盛",
            "events": [
                ("public_expression", 15),
                ("travel_traffic", 10),
                ("relationship_progress", 10),
            ],
        },
        "autumn": {
            "months": [7, 8, 9],
            "elements": ["金"],
            "label": "秋季·收敛",
            "events": [
                ("contract_document", 15),
                ("project_progress", 15),
                ("legal_compliance", 10),
            ],
        },
        "winter": {
            "months": [10, 11, 12],
            "elements": ["水"],
            "label": "冬季·收藏",
            "events": [("sleep_issue", 15), ("emotional_pressure", 10), ("kidney_fatigue", 10)],
        },
    }
    events = []
    for season, info in season_map.items():
        if month_num in info["months"]:
            for etype, bonus in info["events"]:
                if _is_favorable(gan_element, favorable):
                    events.append(
                        {"event_type": etype, "bonus": bonus, "season_label": info["label"]}
                    )
    return events


def _check_major_event_conditions(
    event_type: str, matched_count: int, total_conditions: int
) -> bool:
    """检查大事件是否满足最少触发条件数。"""
    min_required = {
        "property_housing": 2,
        "travel_traffic": 2,
        "wealth_inflow": 2,
        "wealth_outflow": 2,
    }
    req = min_required.get(event_type, 1)
    return matched_count >= req


def postprocess_monthly_events(all_results: list[dict]) -> list[dict]:
    """对12个月流月事件做差异化后处理。"""
    if not all_results:
        return all_results

    # 1. 统计每个 event_type 出现次数
    event_counts = {}
    for r in all_results:
        for e in r.get("top_events", []):
            et = e.get("event_type", "")
            event_counts[et] = event_counts.get(et, 0) + 1

    # 2. 对超出6次的事件类型进行降分
    overused = {k: v for k, v in event_counts.items() if v > 6}
    if overused:
        preserved_bridge_types: set[str] = set()
        for r in all_results:
            retained_events = []
            for event in r["top_events"]:
                event_type = str(event.get("event_type", ""))
                if event_type not in overused:
                    retained_events.append(event)
                elif event.get("from_bridge") and event_type not in preserved_bridge_types:
                    retained_events.append(event)
                    preserved_bridge_types.add(event_type)
            r["top_events"] = retained_events
            # 补回被移除事件后的空位
            if len(r["top_events"]) < 2:
                score_map = r.get("event_score_map", {})
                remaining = sorted(
                    [(k, v) for k, v in score_map.items() if k not in overused], key=lambda x: -x[1]
                )
                for et, sc in remaining[:2]:
                    evt_info = EVENT_TYPES.get(et, {"label": et, "category": "其他"})
                    r["top_events"].append(
                        {
                            "event_type": et,
                            "label": evt_info["label"],
                            "category": evt_info["category"],
                            "probability_level": "需观察",
                            "score": sc,
                            "reason": "作为月度事件补充参考。",
                            "advice": _generate_advice(et),
                            "source_ids": ["yuan_hai_zi_ping"],
                        }
                    )

    # 3. 检查相邻月份事件是否连续重复
    for i in range(1, len(all_results)):
        prev_types = [e["event_type"] for e in all_results[i - 1].get("top_events", [])[:3]]
        curr_types = [e["event_type"] for e in all_results[i].get("top_events", [])[:3]]
        if prev_types and curr_types and prev_types == curr_types:
            # 换掉当前月份中与上月重复的事件
            curr = all_results[i]
            score_map = curr.get("event_score_map", {})
            alternatives = [
                (k, v)
                for k, v in sorted(score_map.items(), key=lambda x: -x[1])
                if k not in prev_types and v >= 20
            ]
            if alternatives:
                worst_evt = min(curr["top_events"], key=lambda x: x["score"])
                et, sc = alternatives[0]
                evt_info = EVENT_TYPES.get(et, {"label": et, "category": "其他"})
                curr["top_events"].remove(worst_evt)
                curr["top_events"].append(
                    {
                        "event_type": et,
                        "label": evt_info["label"],
                        "category": evt_info["category"],
                        "probability_level": "需观察",
                        "score": sc,
                        "reason": "作为月度差异化补充事件。",
                        "advice": _generate_advice(et),
                        "source_ids": ["yuan_hai_zi_ping"],
                    }
                )

    # 4. 相隔较远的月份也不能出现完全相同的 Top 3 组合。
    seen_top_sets: set[frozenset[str]] = set()
    for result in all_results:
        events = list(result.get("top_events", []))
        if len(events) < 3:
            continue
        signature = frozenset(str(event.get("event_type", "")) for event in events[:3])
        if signature in seen_top_sets:
            current_types = {str(event.get("event_type", "")) for event in events[:3]}
            replace_index = min(
                range(3), key=lambda index: float(events[index].get("score", 0) or 0)
            )
            score_map = result.get("event_score_map", {})
            alternatives = sorted(score_map.items(), key=lambda item: -float(item[1] or 0))
            for event_type, score in alternatives:
                if event_type in current_types or float(score or 0) < 20:
                    continue
                candidate_types = set(current_types)
                candidate_types.discard(str(events[replace_index].get("event_type", "")))
                candidate_types.add(str(event_type))
                candidate_signature = frozenset(candidate_types)
                if candidate_signature in seen_top_sets:
                    continue
                event_info = EVENT_TYPES.get(event_type, {"label": event_type, "category": "其他"})
                events[replace_index] = {
                    "event_type": event_type,
                    "label": event_info["label"],
                    "category": event_info["category"],
                    "probability_level": "需观察",
                    "score": score,
                    "reason": "作为全年节奏差异化补充事件。",
                    "advice": _generate_advice(event_type),
                    "source_ids": ["yuan_hai_zi_ping"],
                }
                result["top_events"] = events
                signature = candidate_signature
                break
        seen_top_sets.add(signature)

    for r in all_results:
        r["top_events"] = [
            e
            if e.get("from_bridge")
            else _enrich_event_payload(
                e,
                ten_god=r.get("ten_god", ""),
                gan_element=r.get("gan_element", ""),
                zhi_element=r.get("zhi_element", ""),
                has_clash=bool(r.get("month_unique_triggers")),
            )
            for e in r.get("top_events", [])
        ]

    return all_results


def build_year_monthly_event_results(
    chart: dict,
    monthly_data: list[dict],
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> list[dict]:
    """生成全年 12 个月统一流月事件推断结果。"""
    results = [
        infer_monthly_likely_events(chart, item, yearly_data, luck_data) for item in monthly_data
    ]
    return postprocess_monthly_events(results)


def infer_monthly_likely_events_enhanced(
    chart: dict,
    monthly_item: dict,
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
    prev_month_events: list | None = None,
) -> dict:
    """
    增强版流月事件推断：结合十神事件池、地支冲击领域、季节加成、严格触发条件。
    """
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = strength.get("favorable_elements", []) or []
    unfavorable = strength.get("unfavorable_elements", []) or []
    ten_god_counts = chart.get("ten_god_counts", {}) or {}
    month_num = monthly_item.get("month", 1)

    gan = monthly_item.get("gan", "")
    zhi = monthly_item.get("zhi", "")
    ten_god = monthly_item.get("ten_god", "")
    gan_element = STEM_ELEMENTS.get(gan, "")
    zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
    from ..bazi.branch_relations import analyze_year_branch_relations

    branch_rels = monthly_item.get("branch_relations", analyze_year_branch_relations(chart, zhi))
    has_clash = monthly_item.get(
        "has_clash",
        any(r.get("relation_type") == "六冲" for r in branch_rels) if branch_rels else False,
    )

    # ---- Step 1: 十神主事件池（权重优先） ----
    ten_god_pools = {
        "比肩": [
            "cooperation",
            "social_drinking",
            "cooperation_money",
            "relationship_conflict",
            "cooperation_boundary",
            "old_contact",
        ],
        "劫财": [
            "social_drinking",
            "favor_obligation",
            "debt_loss",
            "cooperation_money",
            "wealth_outflow",
            "relationship_conflict",
            "old_contact",
            "overwork",
        ],
        "食神": [
            "public_expression",
            "business_surprise",
            "study_exam",
            "project_progress",
            "digestion_issue",
        ],
        "伤官": [
            "public_expression",
            "contract_document",
            "official_dispute",
            "relationship_conflict",
            "legal_compliance",
            "emotional_pressure",
            "fire_anxiety",
        ],
        "正财": [
            "client_payment",
            "wealth_inflow",
            "shop_property",
            "asset_purchase",
            "property_housing",
            "investment_risk",
            "vehicle_expense",
        ],
        "偏财": [
            "business_surprise",
            "client_payment",
            "wealth_inflow",
            "cooperation_money",
            "investment_risk",
            "debt_loss",
            "travel_delay",
            "cashflow_pressure",
        ],
        "正官": [
            "contract_document",
            "official_dispute",
            "boss_pressure",
            "career_change",
            "legal_compliance",
        ],
        "七杀": [
            "vehicle_safety",
            "official_dispute",
            "illness_symbol_attention",
            "contract_document",
            "career_change",
            "medical_attention",
            "safety_attention",
            "emotional_pressure",
            "fire_anxiety",
            "respiratory_skin",
            "overwork",
            "travel_delay",
        ],
        "正印": [
            "study_exam",
            "property_housing",
            "shop_property",
            "family_issue",
            "asset_purchase",
            "sleep_issue",
            "home_repair",
            "family_asset",
        ],
        "偏印": [
            "study_exam",
            "illness_symbol_attention",
            "property_housing",
            "medical_attention",
            "emotional_pressure",
            "kidney_fatigue",
        ],
    }
    primary_pool = ten_god_pools.get(
        ten_god, ["wealth_inflow", "contract_document", "health_fluctuation"]
    )

    # ---- Step 2: 构建事件评分 ----
    event_scores = {}
    event_triggers = {}
    is_cai = ten_god in ("正财", "偏财")
    is_shishen = ten_god in ("食神", "伤官")
    is_bi_jie = ten_god in ("比肩", "劫财")
    is_guan = ten_god in ("正官", "七杀")
    is_yin = ten_god in ("正印", "偏印")

    is_bi = ten_god in ("比肩", "劫财")
    for evt_type in list(EVENT_TYPES.keys()):
        matched = 0
        total = 1
        factors = []
        score = 15  # base

        # ---- 财运进入 ----
        if evt_type == "wealth_inflow":
            total = 6
            if is_cai:
                matched += 1
                factors.append("财星被引动")
            if _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append("流月五行为喜用")
            if is_shishen:
                matched += 1
                factors.append("食伤生财")
            if yearly_data and yearly_data.get("relation_to_favorable") == "喜用相关":
                matched += 1
                factors.append("年度喜用相关")
            if is_cai and not has_clash:
                matched += 1
                factors.append("财星平稳无冲")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 10

        # ---- 支出破财 ----
        elif evt_type == "wealth_outflow":
            total = 6
            if is_cai and _is_unfavorable(gan_element, unfavorable):
                matched += 1
                factors.append("财星为忌")
            if is_bi_jie:
                matched += 1
                factors.append("比劫制财")
            if has_clash and _is_unfavorable(zhi_element, unfavorable):
                matched += 1
                factors.append("冲+忌神")
            if ten_god_counts.get("偏财", 0) > ten_god_counts.get("正财", 0) + 1:
                matched += 1
                factors.append("偏财偏重")
            if is_bi_jie and has_clash:
                matched += 1
                factors.append("比劫+冲")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 10

        # ---- 客户回款/订单收益 ----
        elif evt_type == "client_payment":
            total = 6
            if is_cai:
                matched += 1
                factors.append("财星被引动")
            if is_shishen:
                matched += 1
                factors.append("食伤生财")
            if _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append("喜用助力")
            if yearly_data and yearly_data.get("relation_to_favorable") == "喜用相关":
                matched += 1
                factors.append("年度喜用相关")
            if not has_clash and is_cai:
                matched += 1
                factors.append("财星平稳利结算")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 破财漏财/借支担保 ----
        elif evt_type == "debt_loss":
            total = 6
            if is_bi_jie:
                matched += 1
                factors.append("比劫制财")
            if is_cai and _is_unfavorable(gan_element, unfavorable):
                matched += 1
                factors.append("财星为忌")
            if has_clash:
                matched += 1
                factors.append("冲动带来计划外支出")
            if ten_god_counts.get("偏财", 0) > ten_god_counts.get("正财", 0):
                matched += 1
                factors.append("偏财机会伴随波动")
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                matched += 1
                factors.append("忌神参与")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 房产居住 ----
        elif evt_type == "property_housing":
            total = 6
            is_tu = zhi_element == "土" or gan_element == "土"
            has_day_clash = has_clash and zhi == chart.get("pillars", {}).get("day", {}).get(
                "zhi", ""
            )
            if is_tu:
                matched += 1
                factors.append("流月土旺")
            if is_yin and _is_favorable(gan_element, favorable):
                matched += 1
                factors.append(f"印星+喜用")
            if is_cai and _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append(f"财星+喜用")
            if has_day_clash:
                matched += 1
                factors.append("冲日支居住")
            if is_tu and has_clash:
                matched += 1
                factors.append("土+冲")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 10

        # ---- 房车店铺/大件添置 ----
        elif evt_type == "asset_purchase":
            total = 6
            is_tu = zhi_element == "土" or gan_element == "土"
            if is_cai:
                matched += 1
                factors.append("财星动资产")
            if is_tu:
                matched += 1
                factors.append("土象房产店铺")
            if is_yin:
                matched += 1
                factors.append("印星主承载")
            if has_clash and zhi == chart.get("pillars", {}).get("day", {}).get("zhi", ""):
                matched += 1
                factors.append("冲日支居住")
            if _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append("喜用助力")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 店铺门面/经营场地 ----
        elif evt_type == "shop_property":
            total = 6
            is_tu = zhi_element == "土" or gan_element == "土"
            if is_cai:
                matched += 1
                factors.append("财星带动经营")
            if is_tu:
                matched += 1
                factors.append("土象场地事务")
            if is_yin:
                matched += 1
                factors.append("印星主固定资源")
            if ten_god in ("正财", "偏财", "正印", "偏印"):
                matched += 1
                factors.append(f"{ten_god}关联经营承载")
            if _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append("喜用助力")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 出行交通 ----
        elif evt_type == "travel_traffic":
            total = 5
            has_year_hour_clash = has_clash and (
                zhi == chart.get("pillars", {}).get("year", {}).get("zhi", "")
                or zhi == chart.get("pillars", {}).get("hour", {}).get("zhi", "")
            )
            if has_year_hour_clash:
                matched += 1
                factors.append("冲年/时支出行")
            if (
                has_clash
                and _is_unfavorable(gan_element, unfavorable)
                and _is_unfavorable(zhi_element, unfavorable)
            ):
                matched += 1
                factors.append("冲+忌神出行")
            if ten_god in ("偏财", "七杀"):
                matched += 1
                factors.append(f"{ten_god}动象")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 车辆驾驶/安全 ----
        elif evt_type == "vehicle_safety":
            total = 6
            has_year_hour_clash = has_clash and (
                zhi == chart.get("pillars", {}).get("year", {}).get("zhi", "")
                or zhi == chart.get("pillars", {}).get("hour", {}).get("zhi", "")
            )
            if has_year_hour_clash:
                matched += 1
                factors.append("冲年/时支出行")
            if ten_god == "七杀":
                matched += 1
                factors.append("七杀压力")
            if has_clash:
                matched += 1
                factors.append("地支冲动")
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                matched += 1
                factors.append("忌神参与")
            if gan_element in ("火", "金") or zhi_element in ("火", "金"):
                matched += 1
                factors.append("火金工具象")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 合同文书 ----
        elif evt_type == "contract_document":
            total = 5
            if is_guan and _is_unfavorable(gan_element, unfavorable):
                matched += 1
                factors.append("官杀为忌")
            if ten_god == "伤官":
                matched += 1
                factors.append("伤官见官")
            if has_clash and zhi == chart.get("pillars", {}).get("month", {}).get("zhi", ""):
                matched += 1
                factors.append("冲月支工作")
            if is_guan:
                matched += 1
                factors.append(f"{ten_god}官杀")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 官非口舌/罚单投诉 ----
        elif evt_type == "official_dispute":
            total = 6
            if is_guan:
                matched += 1
                factors.append("官杀规则压力")
            if ten_god == "伤官":
                matched += 1
                factors.append("伤官表达冲规则")
            if ten_god == "七杀" and has_clash:
                matched += 1
                factors.append("七杀遇冲")
            if gan_element == "金" or zhi_element == "金":
                matched += 1
                factors.append("金象规则罚单")
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                matched += 1
                factors.append("忌神参与")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 感情推进 ----
        elif evt_type == "relationship_progress":
            total = 4
            is_cai_guan = ten_god in ("正财", "偏财", "正官", "七杀")
            if is_cai_guan and _is_favorable(gan_element, favorable):
                matched += 1
                factors.append("财官+喜用")
            if zhi in ("子", "午", "卯", "酉"):
                matched += 1
                factors.append(f"梅花{zhi}")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 感情摩擦 ----
        elif evt_type == "relationship_conflict":
            total = 5
            if has_clash and zhi == chart.get("pillars", {}).get("day", {}).get("zhi", ""):
                matched += 1
                factors.append("冲日支配偶宫")
            if is_bi_jie and ten_god_counts.get("劫财", 0) > 1:
                matched += 1
                factors.append("劫财过重")
            if ten_god == "伤官" and ten_god_counts.get("伤官", 0) > 1:
                matched += 1
                factors.append("伤官过重")
            if has_clash and _is_unfavorable(zhi_element, unfavorable):
                matched += 1
                factors.append("冲+忌神关系")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 健康波动 ----
        elif evt_type == "health_fluctuation":
            total = 4
            over_weak = any(_is_unfavorable(e, unfavorable) for e in [gan_element, zhi_element])
            if over_weak:
                matched += 1
                factors.append("流月为忌神")
            if is_guan and _is_unfavorable(gan_element, unfavorable):
                matched += 1
                factors.append(f"{ten_god}压力")
            if has_clash and _is_unfavorable(zhi_element, unfavorable):
                matched += 1
                factors.append("冲+忌神健康")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 病符小疾/体检复查 ----
        elif evt_type == "illness_symbol_attention":
            total = 6
            over_weak = any(_is_unfavorable(e, unfavorable) for e in [gan_element, zhi_element])
            if over_weak:
                matched += 1
                factors.append("忌神压身")
            if is_guan:
                matched += 1
                factors.append(f"{ten_god}压力")
            if has_clash:
                matched += 1
                factors.append("冲动身体状态")
            if gan_element in ("火", "土", "金") or zhi_element in ("火", "土", "金"):
                matched += 1
                factors.append("火土金压力")
            if is_yin:
                matched += 1
                factors.append("印星调养信号")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 身体检查/小病早看 ----
        elif evt_type == "medical_attention":
            total = 5
            over_weak = any(_is_unfavorable(e, unfavorable) for e in [gan_element, zhi_element])
            if over_weak:
                matched += 1
                factors.append("忌神压身")
            if is_guan:
                matched += 1
                factors.append(f"{ten_god}压力")
            if is_yin:
                matched += 1
                factors.append("印星调养")
            if has_clash:
                matched += 1
                factors.append("冲动身体宫位")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 学习考试 ----
        elif evt_type == "study_exam":
            total = 4
            if is_yin and _is_favorable(gan_element, favorable):
                matched += 1
                factors.append("印星+喜用")
            if _is_favorable(zhi_element, favorable) and is_yin:
                matched += 1
                factors.append("地支喜用")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 合作 ----
        elif evt_type == "cooperation":
            total = 4
            if is_bi and has_clash:
                matched += 1
                factors.append("比劫+冲")
            if is_bi and _is_favorable(gan_element, favorable):
                matched += 1
                factors.append("比劫+喜用")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 酒局人情/朋友应酬 ----
        elif evt_type == "social_drinking":
            total = 5
            if is_bi_jie:
                matched += 1
                factors.append("比劫朋友人情")
            if zhi in ("子", "午", "卯", "酉"):
                matched += 1
                factors.append("桃花地支人际")
            if has_clash and zhi == chart.get("pillars", {}).get("day", {}).get("zhi", ""):
                matched += 1
                factors.append("冲日支口舌")
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                matched += 1
                factors.append("忌神带来消耗")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 人情请托/朋友求助 ----
        elif evt_type == "favor_obligation":
            total = 6
            if is_bi_jie:
                matched += 1
                factors.append("比劫朋友同辈")
            if ten_god == "劫财":
                matched += 1
                factors.append("劫财人情资源")
            if has_clash:
                matched += 1
                factors.append("冲动关系位")
            if _is_unfavorable(gan_element, unfavorable) or _is_unfavorable(
                zhi_element, unfavorable
            ):
                matched += 1
                factors.append("忌神带来消耗")
            if ten_god_counts.get("劫财", 0) + ten_god_counts.get("比肩", 0) >= 2:
                matched += 1
                factors.append("原局比劫不弱")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 家庭事务/长辈事务 ----
        elif evt_type == "family_issue":
            total = 6
            is_tu = zhi_element == "土" or gan_element == "土"
            if has_clash and zhi == chart.get("pillars", {}).get("year", {}).get("zhi", ""):
                matched += 1
                factors.append("冲年支家庭位")
            if is_yin:
                matched += 1
                factors.append("印星家庭承载")
            if is_tu:
                matched += 1
                factors.append("土象家宅")
            if has_clash:
                matched += 1
                factors.append("冲动旧事")
            if ten_god in ("正印", "偏印", "正财", "偏财"):
                matched += 1
                factors.append(f"{ten_god}关联家庭资产")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 11

        # ---- 项目财务转机 ----
        elif evt_type == "business_surprise":
            total = 5
            if is_cai:
                matched += 1
                factors.append("财星机会")
            if is_shishen:
                matched += 1
                factors.append("食伤生财")
            if _is_favorable(gan_element, favorable) or _is_favorable(zhi_element, favorable):
                matched += 1
                factors.append("喜用助力")
            if yearly_data and yearly_data.get("relation_to_favorable") == "喜用相关":
                matched += 1
                factors.append("年度喜用加持")
            if evt_type in primary_pool:
                matched += 1
                factors.append(f"十神<{ten_god}>主事件池")
            score = 15 + matched * 12

        # ---- 其他事件默认评分 ----
        else:
            if evt_type in primary_pool:
                matched = 1
                score = 25
                factors.append(f"十神<{ten_god}>主事件")
            else:
                continue

        min_required = REALITY_EVENT_RULES.get(evt_type, {}).get("min_trigger_count", 1)
        if matched < min_required:
            score = min(score, 21)
        event_scores[evt_type] = min(100, score)
        event_triggers[evt_type] = factors

    # ---- Step 3: 地支冲击事件加分 ----
    if has_clash:
        clash_events = _get_clash_driven_events(
            zhi, chart, ten_god, gan_element, zhi_element, favorable, unfavorable
        )
        for ce in clash_events:
            et = ce["event_type"]
            if et not in event_scores or ce["score"] > event_scores[et]:
                event_scores[et] = ce["score"]
                event_triggers[et] = ce.get("trigger_factors", ["地支冲击"])

    # ---- Step 4: 季节事件加分 ----
    season_events = _get_season_events(month_num, gan_element, zhi_element, favorable)
    for se in season_events:
        et = se["event_type"]
        if et in event_scores:
            event_scores[et] = min(100, event_scores[et] + se.get("bonus", 5))
            event_triggers.setdefault(et, []).append(se.get("season_label", "季节"))

    # ---- Step 5: 筛选 Top Events ----
    sorted_events = sorted(event_scores.items(), key=lambda x: -x[1])
    top_events = []
    for evt_type, score in sorted_events:
        if len(top_events) >= 5:
            break
        if score < 22:
            continue
        evt_info = EVENT_TYPES.get(evt_type, {"label": evt_type, "category": "其他"})
        probability_level = "较高" if score >= 60 else "中等" if score >= 38 else "需观察"
        factors = event_triggers.get(evt_type, [])

        top_events.append(
            _enrich_event_payload(
                {
                    "event_type": evt_type,
                    "label": evt_info["label"],
                    "category": evt_info["category"],
                    "probability_level": probability_level,
                    "score": round(score, 1),
                    "reason": _generate_reason(
                        evt_type, ten_god, gan_element, zhi_element, has_clash, zhi
                    ),
                    "advice": _generate_advice(evt_type),
                    "trigger_factors": factors,
                    "source_ids": EXTENDED_SOURCE_IDS,
                },
                ten_god,
                gan_element,
                zhi_element,
                has_clash,
            )
        )

    # ---- Step 6: 事件去重与补充 ----
    # 如果主事件池事件没有进入top_events，加入补充
    seen_types = {e["event_type"] for e in top_events}
    for pe in primary_pool:
        if pe not in seen_types and pe in event_scores and event_scores[pe] >= 22:
            evt_info = EVENT_TYPES.get(pe, {"label": pe, "category": "其他"})
            top_events.append(
                _enrich_event_payload(
                    {
                        "event_type": pe,
                        "label": evt_info["label"],
                        "category": evt_info["category"],
                        "probability_level": "需观察",
                        "score": event_scores[pe],
                        "reason": f"流月十神<{ten_god}>主事件集中区，相关事务容易被触发。",
                        "advice": _generate_advice(pe),
                        "trigger_factors": [f"十神<{ten_god}>主事件池"],
                        "source_ids": EXTENDED_SOURCE_IDS,
                    },
                    ten_god,
                    gan_element,
                    zhi_element,
                    has_clash,
                )
            )
            seen_types.add(pe)
        if len(top_events) >= 4:
            break

    # ---- Step 7: 来源与依据 ----
    source_titles = _source_titles(EXTENDED_SOURCE_IDS)
    basis_text = f"流月十神为{ten_god}，天干{gan}({gan_element})，地支{zhi}({zhi_element})，"
    if primary_pool:
        basis_text += f"十神主事件集中在{'、'.join(primary_pool[:3])}。"
    if has_clash:
        basis_text += f"地支冲动存在，容易激发该宫位对应事务。"
    season_label = next((s["season_label"] for s in season_events), "")
    if season_label:
        basis_text += f"季节因素<{season_label}>。"

    return {
        "month": month_num,
        "pillar": monthly_item.get("pillar", ""),
        "ten_god": ten_god,
        "gan_element": gan_element,
        "zhi_element": zhi_element,
        "relation_to_favorable": "喜用相关"
        if any(_is_favorable(e, favorable) for e in [gan_element, zhi_element])
        else "忌神相关"
        if any(_is_unfavorable(e, unfavorable) for e in [gan_element, zhi_element])
        else "平稳观察",
        "month_theme": primary_pool[0] if primary_pool else "",
        "top_events": top_events[:5],
        "event_score_map": {k: round(v, 1) for k, v in sorted(event_scores.items())},
        "month_unique_triggers": event_triggers,
        "basis": basis_text,
        "source_ids": EXTENDED_SOURCE_IDS,
        "source_titles": source_titles,
    }


# 向后兼容别名
infer_monthly_likely_events = infer_monthly_likely_events_enhanced

# ====== v1.3-A2 事件变体池 + 证据链校验 ======

import json as _json
import os as _os

# 变体池加载
_VARIANT_POOLS: dict = {}


def _load_variant_pools() -> dict:
    import json, os

    path = os.path.join(os.path.dirname(__file__), "rules", "monthly_event_variants.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_VARIANT_POOLS = _load_variant_pools()

# v1.3-A3: 规则库加载
import json as _json
import os as _os

_ONTOLOGY: dict = {}
_TRIGGER_RULES: list = []
_SPECIFIC_RULES: list = []


def _load_event_ontology() -> dict:
    path = _os.path.join(_os.path.dirname(__file__), "rules", "monthly_event_ontology.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return {}


def _load_trigger_rules() -> list:
    path = _os.path.join(_os.path.dirname(__file__), "rules", "monthly_event_trigger_rules.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return []


def _load_specific_rules() -> list:
    path = _os.path.join(_os.path.dirname(__file__), "rules", "monthly_specific_event_rules.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return []


def _reload_all_rules():
    global _ONTOLOGY, _TRIGGER_RULES, _SPECIFIC_RULES
    _ONTOLOGY = _load_event_ontology()
    _TRIGGER_RULES = _load_trigger_rules()
    _SPECIFIC_RULES = _load_specific_rules()


_ONTOLOGY = _load_event_ontology()
_TRIGGER_RULES = _load_trigger_rules()
_SPECIFIC_RULES = _load_specific_rules()
for _event_type, _event_info in _ONTOLOGY.items():
    EVENT_TYPES[_event_type] = {
        "label": _event_info.get("label", _event_type),
        "category": _event_info.get("category", "其他"),
    }


def _match_rules_for_event(event_type: str, context: dict) -> list:
    """匹配触发规则，返回命中的规则列表。"""
    hits = []
    for rule in _TRIGGER_RULES:
        if rule.get("target_event_type") == event_type:
            conditions = rule.get("trigger_conditions", [])
            matched = 0
            for cond in conditions:
                ctype = cond.get("type", "")
                cval = cond.get("value", [])
                if ctype == "ten_god" and context.get("ten_god", "") in cval:
                    matched += 1
                elif (
                    ctype == "favorable_relation"
                    and context.get("relation_to_favorable", "") == cval
                ):
                    matched += 1
            if matched >= rule.get("min_trigger_count", 1):
                hits.append(rule)
    return hits


def _get_source_ids_for_event(event_type: str, context: dict) -> list:
    """从命中的规则获取 source_ids。"""
    rules = _match_rules_for_event(event_type, context)
    if rules:
        return rules[0].get("source_ids", [])
    ontology = _ONTOLOGY.get(event_type, {})
    return ontology.get("source_ids", ["yuanhai_ziping", "sanming_tonghui", "mingli_tanyuan"])


def _select_event_variant(event_type: str, evidence: list) -> dict | None:
    """根据证据链选择匹配的变体，无匹配则返回默认变体。"""
    variants = _VARIANT_POOLS.get(event_type, [])
    if not variants:
        return None
    # 精确匹配：变体的 trigger_pattern 中所有项都出现在 evidence 中
    for v in variants:
        pattern = v.get("trigger_pattern", [])
        if pattern and any(pat in "|".join(evidence) for pat in pattern):
            return v
    # 默认：使用第一个 variant（通常是 trigger_pattern 为空的通用版）
    if variants:
        return variants[0]
    return None


def _apply_variant_to_event(event: dict, evidence: list) -> dict:
    """将变体数据应用到事件对象。"""
    variant = _select_event_variant(event.get("event_type", ""), evidence)
    if variant:
        event["one_line"] = variant.get("one_line", event.get("plain_summary", ""))
        if not event.get("plain_summary"):
            event["plain_summary"] = variant.get("one_line", "")
        event["real_world_signals"] = variant.get(
            "real_world_signals", event.get("real_world_signals", [])
        )
        event["risk_points"] = variant.get("risk_points", event.get("risk_points", []))
        event["advice"] = variant.get("advice", event.get("advice", ""))
        event["variant_id"] = variant.get("variant_id", "")
    return event
