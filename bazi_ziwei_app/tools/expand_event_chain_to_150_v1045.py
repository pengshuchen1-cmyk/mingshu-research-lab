"""Expand evidence-chain event coverage from 98 to about 150.

Scope is intentionally limited:
- priority blocks: business operation, family/elder, risk/loss
- adjacent practical blocks: traffic, housing, social
- no new event_type is added
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
]

COMMON_PALACE = {
    "year_branch": "年支偏向长辈、家庭背景、外部圈层和旧有关系。",
    "month_branch": "月支偏向事业平台、上级同事、客户组织和主业环境。",
    "day_branch": "日支偏向伴侣、合作方、一对一关系和居住状态。",
    "hour_branch": "时支偏向项目结果、副业、晚辈、长期规划和收尾事项。",
}

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


EVENT_GROUPS: dict[str, list[str]] = {
    "business": [
        "store_operation",
        "customer_growth",
        "customer_complaint",
        "supplier_issue",
        "inventory_pressure",
        "pricing_adjustment",
        "marketing_exposure",
        "content_traffic",
        "account_growth",
        "business_partnership",
        "business_negotiation",
        "operation_cost",
    ],
    "family": [
        "family_issue",
        "elder_issue",
        "family_discussion",
        "family_asset_discussion",
        "household_repair",
        "sibling_relative_issue",
        "parent_health_attention",
        "family_responsibility",
    ],
    "risk": [
        "minor_loss",
        "delayed_issue",
        "misunderstanding_risk",
        "rule_penalty",
        "impulsive_decision",
        "overcommitment",
        "hidden_cost",
        "emotional_spending",
        "equipment_fault",
        "document_missing",
    ],
    "traffic": [
        "travel_delay",
        "business_trip",
        "vehicle_safety",
        "safety_attention",
        "traffic_ticket",
        "parking_insurance",
        "route_change",
        "long_distance_travel",
        "travel_document",
    ],
    "housing": [
        "house_viewing",
        "renovation_equipment",
        "appliance_issue",
        "family_asset",
        "landlord_tenant",
        "property_contract",
        "living_environment_change",
    ],
    "social": [
        "friend_request",
        "reputation_attention",
        "gossip_dispute",
        "gift_expense",
        "banquet_party",
        "old_friend_contact",
    ],
}

EVENT_DETAILS: dict[str, dict[str, Any]] = {
    "store_operation": {"scene": "门店经营、客流、账目和日常运营", "positive": "门店经营节奏变顺", "neutral": "需要重新看客流、排班和账目", "negative": "经营成本或现场事务增多"},
    "customer_growth": {"scene": "客户增长、复购、转介绍和新客入口", "positive": "客户数量或咨询量增加", "neutral": "新线索变多但需要筛选", "negative": "客户增长伴随服务压力"},
    "customer_complaint": {"scene": "客户投诉、售后、评价和服务补救", "positive": "问题被及时解释并修复", "neutral": "客户反馈需要耐心处理", "negative": "投诉、差评或售后压力增加"},
    "supplier_issue": {"scene": "供应商、进货、交期和质量稳定度", "positive": "供应链协调有改善", "neutral": "供货时间和价格需要再确认", "negative": "供应商变卦、延迟或质量不稳"},
    "inventory_pressure": {"scene": "库存、补货、压货和周转", "positive": "库存结构被重新理顺", "neutral": "需要盘点库存和现金占用", "negative": "压货、积压或补货压力增加"},
    "pricing_adjustment": {"scene": "价格调整、折扣、报价和毛利", "positive": "价格策略更清楚", "neutral": "需要测算客户接受度", "negative": "降价压力或利润被压缩"},
    "marketing_exposure": {"scene": "宣传曝光、广告、活动和品牌展示", "positive": "宣传曝光更容易被看见", "neutral": "曝光增加但转化还要跟进", "negative": "花了推广费但转化慢"},
    "content_traffic": {"scene": "内容流量、浏览、点赞和传播", "positive": "内容流量提升", "neutral": "流量有波动，需要看转化", "negative": "有热度但客户转化不足"},
    "account_growth": {"scene": "账号涨粉、私域沉淀和用户互动", "positive": "账号粉丝或关注增长", "neutral": "互动增加但质量要筛选", "negative": "涨粉虚热或维护压力增加"},
    "business_partnership": {"scene": "商业合作、合伙、渠道和资源置换", "positive": "合作资源出现", "neutral": "合作条件需要谈清楚", "negative": "合作边界不清或分账压力"},
    "business_negotiation": {"scene": "商务谈判、报价、条件交换和合作推进", "positive": "谈判有推进空间", "neutral": "对方仍在比较条件", "negative": "谈判反复或要求增加"},
    "operation_cost": {"scene": "经营成本、租金、人力、平台和耗材", "positive": "成本结构被看清", "neutral": "需要重新做预算", "negative": "经营成本上升或隐藏费用出现"},
    "family_issue": {"scene": "家庭事务、家中安排和亲属沟通", "positive": "家庭事务能被协调", "neutral": "家中安排需要花时间处理", "negative": "家庭琐事占用精力"},
    "elder_issue": {"scene": "长辈事务、长辈意见和照应安排", "positive": "长辈事项有明确安排", "neutral": "需要听取长辈意见但保留判断", "negative": "长辈事务带来责任和时间压力"},
    "family_discussion": {"scene": "家庭商议、计划协调和共同决定", "positive": "家庭讨论能形成共识", "neutral": "家人意见需要慢慢整合", "negative": "意见不一导致反复沟通"},
    "family_asset_discussion": {"scene": "家庭资产、房产、车辆、存款和分配", "positive": "家庭资产议题有推进", "neutral": "金额和权责需要说清楚", "negative": "资产分配或支出意见分歧"},
    "household_repair": {"scene": "家中维修、家电、装修和居住环境", "positive": "家中问题能及时修好", "neutral": "需要安排维修和费用", "negative": "维修反复或预算增加"},
    "sibling_relative_issue": {"scene": "兄弟亲戚、同辈亲属和人情往来", "positive": "亲戚兄弟之间能互相照应", "neutral": "亲属事务需要保持边界", "negative": "亲戚人情或意见牵扯增多"},
    "parent_health_attention": {"scene": "父母状态、作息、体检和陪伴", "positive": "适合主动关心父母状态", "neutral": "父母身体和情绪需要观察", "negative": "父母状态让你分心或担心"},
    "family_responsibility": {"scene": "家庭责任、照顾安排和现实分担", "positive": "责任分工更清楚", "neutral": "需要重新分配时间和资源", "negative": "家庭责任加重或压力上升"},
    "minor_loss": {"scene": "小额损耗、遗失、维修和临时账单", "positive": "小损耗能提前止住", "neutral": "零碎支出需要记账", "negative": "小钱不断流出"},
    "delayed_issue": {"scene": "拖延滞后、排队、审批慢和进度卡住", "positive": "延误事项能被重新推动", "neutral": "需要预留更多时间", "negative": "拖延导致成本增加"},
    "misunderstanding_risk": {"scene": "误会风险、表达偏差和信息错位", "positive": "及时解释能减少误会", "neutral": "重要话题需要复述确认", "negative": "话没说清引发摩擦"},
    "rule_penalty": {"scene": "规则处罚、违约、罚款和制度边界", "positive": "提前检查规则可避开损失", "neutral": "需要核对条款和流程", "negative": "罚款、扣分或违约成本增加"},
    "impulsive_decision": {"scene": "冲动决策、临时下单和情绪判断", "positive": "暂停后能做出更稳选择", "neutral": "决策前需要多一轮核对", "negative": "一时冲动带来后悔成本"},
    "overcommitment": {"scene": "承诺过多、任务过满和人情答应", "positive": "适合整理承诺清单", "neutral": "需要判断哪些能做哪些要拒绝", "negative": "答应太多导致压力失控"},
    "hidden_cost": {"scene": "隐藏成本、附加费用和后续维护", "positive": "提前发现隐性费用", "neutral": "报价之外还要看后续成本", "negative": "后续费用超出预期"},
    "emotional_spending": {"scene": "情绪消费、冲动购买和人情支出", "positive": "能看见消费背后的情绪", "neutral": "适合设置预算上限", "negative": "心情影响花钱判断"},
    "equipment_fault": {"scene": "设备故障、工具、手机电脑和机器维修", "positive": "提前维护能减少停摆", "neutral": "设备需要检查保养", "negative": "设备故障影响工作或出行"},
    "document_missing": {"scene": "资料遗漏、证件、合同附件和表格", "positive": "补齐资料后流程能推进", "neutral": "需要逐项核对材料", "negative": "缺文件导致退回或延误"},
    "travel_delay": {"scene": "行程延误、排队、改签和时间安排", "positive": "提前规划能避开延误", "neutral": "出行要留缓冲时间", "negative": "行程被拖慢或临时改动"},
    "business_trip": {"scene": "出差外出、跨城沟通和客户拜访", "positive": "外出能带来业务线索", "neutral": "差旅安排需要提前确认", "negative": "奔波增多且影响休息"},
    "vehicle_safety": {"scene": "驾驶安全、车辆操作和通勤风险", "positive": "提前检查能降低风险", "neutral": "开车骑车要放慢节奏", "negative": "赶时间导致安全压力"},
    "safety_attention": {"scene": "操作安全、工具使用和交通细节", "positive": "留意细节能避开小麻烦", "neutral": "重要操作前多检查一次", "negative": "粗心带来磕碰或损耗"},
    "traffic_ticket": {"scene": "罚单违章、停车、限行和规则提醒", "positive": "提前查规则可避免处罚", "neutral": "路线和停车规则要确认", "negative": "违章罚单或滞纳成本"},
    "parking_insurance": {"scene": "停车保险、车辆手续和费用续期", "positive": "手续补齐更安心", "neutral": "保险停车费用需要核对", "negative": "忘记续费或手续遗漏"},
    "route_change": {"scene": "路线变更、临时绕路和计划调整", "positive": "换路线反而节省时间", "neutral": "路线要准备备选方案", "negative": "临时改路导致赶时间"},
    "long_distance_travel": {"scene": "远行差旅、跨城安排和长途奔波", "positive": "远行能打开新资源", "neutral": "行李证件和时间要提前排", "negative": "长途奔波带来疲劳"},
    "travel_document": {"scene": "出行证件、票据、酒店和预约", "positive": "资料齐全可顺利出行", "neutral": "票据预约需要复核", "negative": "证件遗漏影响行程"},
    "house_viewing": {"scene": "看房、租房、买房和空间比较", "positive": "适合实地看房比较", "neutral": "价格位置和合同要慢慢看", "negative": "急着定房容易忽略细节"},
    "renovation_equipment": {"scene": "装修设备、家具、家电和施工", "positive": "空间改善能提升效率", "neutral": "装修采购要看预算", "negative": "工期或费用超预期"},
    "appliance_issue": {"scene": "家电设备、维修、更换和售后", "positive": "及时维修能恢复便利", "neutral": "需要判断修还是换", "negative": "家电故障带来支出"},
    "family_asset": {"scene": "家庭资产、房车存款和共同安排", "positive": "家庭资产可重新梳理", "neutral": "共同资产需要说清权责", "negative": "资产意见不一引发压力"},
    "landlord_tenant": {"scene": "房东租客、租约、押金和维修责任", "positive": "租约边界能被重新确认", "neutral": "押金维修责任要写清楚", "negative": "房东租客沟通反复"},
    "property_contract": {"scene": "房屋合同、租约、产权和条款", "positive": "合同条款梳理后更稳", "neutral": "需要核对金额日期和责任", "negative": "条款遗漏导致后续麻烦"},
    "living_environment_change": {"scene": "居住环境变化、搬动、邻里和空间调整", "positive": "居住环境有改善机会", "neutral": "生活节奏需要重新适应", "negative": "环境变化带来不适应"},
    "friend_request": {"scene": "朋友求助、借力、人情和边界", "positive": "能帮到朋友也保住边界", "neutral": "需要判断能帮到什么程度", "negative": "朋友请求带来压力"},
    "reputation_attention": {"scene": "名声评价、口碑、他人看法和公开反馈", "positive": "口碑有被看见的机会", "neutral": "别人评价需要筛选", "negative": "评价压力或误读增加"},
    "gossip_dispute": {"scene": "口舌是非、流言、争执和误解", "positive": "少说多核对可降温", "neutral": "信息传来传去要查证", "negative": "口舌争执影响关系"},
    "gift_expense": {"scene": "礼物红包、人情支出和宴请往来", "positive": "人情表达得体能稳关系", "neutral": "礼金预算要提前定", "negative": "红包礼物支出超预算"},
    "banquet_party": {"scene": "宴席聚会、应酬、饭局和邀约", "positive": "聚会能带来关系维护", "neutral": "参加前要看时间和成本", "negative": "应酬过多消耗精力"},
    "old_friend_contact": {"scene": "旧友联系、老客户、旧同事和过去资源", "positive": "旧关系带来新线索", "neutral": "旧人联系需要观察目的", "negative": "旧关系牵出人情压力"},
}

GROUP_BASIS = {
    "business": {
        "ten_god": ["财星主客户、订单、价格、现金流和经营结果。", "食伤主宣传、表达、产品展示和服务交付。", "官杀主规则、投诉、平台制度和经营压力。"],
        "element": ["土象对应店铺、库存、承载和实际经营盘子。", "火象对应曝光、营销和客户热度。", "金象对应定价、规则、工具和供应链结构。"],
        "branch": ["月支代表主业平台、门店、客户组织和经营环境。", "日支代表合作方、核心客户和一对一谈判。"],
        "required": ["财星、食伤、官杀或月支经营环境至少两项共同出现。", "必须结合客户、库存、价格、宣传或供应商等现实场景。"],
        "anti": ["忌神参与较重", "客户承诺不清", "成本和库存未核算", "只看曝光不看转化"],
    },
    "family": {
        "ten_god": ["印星主长辈、照应、家庭保护和文书安顿。", "比劫主兄弟亲戚、同辈亲属和家中分工。", "财星主家庭资产、支出和现实资源分配。"],
        "element": ["土象对应家庭、房屋、承载和责任。", "木象对应长辈身体状态、成长照应和家中计划。"],
        "branch": ["年支偏长辈、父母、家族背景和家庭外部关系。", "日支偏居住状态和共同生活中的一对一关系。"],
        "required": ["年支、印星、比劫、财星或土象至少两项共同出现。", "必须落到长辈、家庭资产、亲戚兄弟或家庭责任等现实场景。"],
        "anti": ["家庭责任过重", "亲属边界不清", "资产金额没有说清", "情绪代替现实安排"],
    },
    "risk": {
        "ten_god": ["官杀主规则、处罚、压力和责任边界。", "比劫主冲动、竞争、朋友牵连和分担压力。", "食伤主表达偏差、承诺过多和沟通误会。"],
        "element": ["金象对应规则、设备、证件和边界。", "火象对应急躁、曝光和情绪反应。", "土象对应资料、流程、成本和延误。"],
        "branch": ["冲动原局地支时，现实中更容易表现为变动、延误、误会或损耗。", "月支偏工作规则，日支偏合作关系，时支偏设备项目和收尾事项。"],
        "required": ["忌神、冲动、官杀、比劫、食伤或金火土取象至少两项共同出现。", "必须落到资料、规则、成本、误会、设备或冲动选择等现实场景。"],
        "anti": ["忌神参与较重", "冲克过强", "证据只来自单一维度", "缺少现实场景支撑"],
    },
    "traffic": {
        "ten_god": ["七杀主速度、压力、突发任务和安全边界。", "偏财可对应车辆、工具、费用和外出成本。", "食伤主移动表达和行程安排。"],
        "element": ["金象对应车辆结构、工具和规则。", "水象对应流动、路线和远行。", "火象对应速度、急躁和赶时间。"],
        "branch": ["月支被冲偏工作出行，时支被冲偏项目收尾和临时路线，日支被冲偏同行或合作安排。"],
        "required": ["冲动、七杀、偏财、金水火取象至少两项共同出现。", "必须落到车辆、路线、证件、票据或差旅等现实场景。"],
        "anti": ["赶时间", "疲劳出行", "证件票据不齐", "冲克过强"],
    },
    "housing": {
        "ten_god": ["印星主房屋、居住、保护和稳定空间。", "财星主资产、租约、购买和现实成本。", "官杀主合同、责任和产权规则。"],
        "element": ["土象对应房屋、装修、土地和承载。", "金象对应家电设备、合同条款和结构。"],
        "branch": ["年支偏家庭房产，日支偏居住状态，月支偏店铺门面或租约环境。"],
        "required": ["土象、印星、财星、官杀或居住宫位至少两项共同出现。", "必须落到看房、装修、家电、租约、房东租客或居住变化。"],
        "anti": ["合同不清", "急着定房", "预算不明", "维修责任不清"],
    },
    "social": {
        "ten_god": ["比劫主朋友、同辈、旧友和圈层互动。", "食伤主表达、饭局、传播和口舌。", "财星主人情支出、礼物红包和资源交换。"],
        "element": ["火象对应曝光、热闹和情绪表达。", "水象对应流动联系和旧关系回流。"],
        "branch": ["桃花支对应人缘、聚会和关系热度，年支偏旧友长辈圈，月支偏职场圈层。"],
        "required": ["比劫、食伤、财星、桃花或社交宫位至少两项共同出现。", "必须落到朋友求助、名声评价、口舌、礼物红包或旧友联系。"],
        "anti": ["人情成本过重", "口头承诺过多", "口舌误会", "边界不清"],
    },
}


def _load(name: str) -> Any:
    return json.loads((RULES_DIR / name).read_text(encoding="utf-8"))


def _save(name: str, data: Any) -> None:
    (RULES_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _condition(ctype: str, *, value: Any | None = None, weight: float = 1.0, evidence_text: str) -> dict[str, Any]:
    item: dict[str, Any] = {
        "type": ctype,
        "weight": weight,
        "evidence_text": evidence_text,
        "source_ids": CORE_SOURCES[:3],
    }
    if value is not None:
        item["value"] = value
    return item


def _conditions_for(event_type: str, group: str) -> list[dict[str, Any]]:
    scene = EVENT_DETAILS[event_type]["scene"]
    if group == "business":
        if event_type in {"customer_complaint", "business_negotiation"}:
            return [
                _condition("is_output_month", evidence_text=f"{scene}需要表达沟通和服务反馈。"),
                _condition("is_officer_month", evidence_text=f"{scene}涉及规则、评价或责任边界。"),
                _condition("clash_month_branch", weight=1.1, evidence_text="月支代表经营环境，被冲动时客户和平台事务更明显。"),
                _condition("element", value=["火", "金"], weight=0.8, evidence_text="火主曝光情绪，金主规则结构。"),
                _condition("group_count_at_least", value=[{"group": "output", "min": 1}], weight=0.8, evidence_text="原局食伤可见，表达和售后沟通更容易成为主题。"),
            ]
        if event_type in {"marketing_exposure", "content_traffic", "account_growth"}:
            return [
                _condition("is_output_month", evidence_text=f"{scene}依赖表达、内容和展示。"),
                _condition("activate_peach_blossom", weight=1.1, evidence_text="人缘与曝光信号被引动。"),
                _condition("branch_in", value=["子", "午", "卯", "酉"], weight=0.8, evidence_text="桃花地支对应传播、热度和可见度。"),
                _condition("group_count_at_least", value=[{"group": "output", "min": 1}], weight=0.8, evidence_text="原局输出能力能承接流量。"),
                _condition("favorable_relation", value=["喜用相关", "平稳观察"], weight=0.7, evidence_text="喜用或平稳月份更适合曝光转化。"),
            ]
        return [
            _condition("is_wealth_month", evidence_text=f"{scene}和客户、订单、成本或现金流有关。"),
            _condition("is_output_month", evidence_text=f"{scene}需要产品、服务或沟通交付。"),
            _condition("clash_month_branch", weight=1.0, evidence_text="月支代表经营平台，被冲动时主业事务更明显。"),
            _condition("group_count_at_least", value=[{"group": "wealth", "min": 1}], weight=0.8, evidence_text="原局财星可见，经营结果更容易落到钱和客户。"),
            _condition("element", value=["土", "金", "火"], weight=0.8, evidence_text="土看店铺库存，金看定价供应，火看曝光热度。"),
        ]
    if group == "family":
        if event_type in {"sibling_relative_issue"}:
            return [
                _condition("is_peer_month", evidence_text=f"{scene}和同辈亲属、兄弟姐妹有关。"),
                _condition("clash_year_branch", weight=1.1, evidence_text="年支代表家庭圈层，被冲动时亲属事务更明显。"),
                _condition("group_count_at_least", value=[{"group": "peer", "min": 1}], weight=0.8, evidence_text="原局比劫可见，亲戚同辈互动更容易被触发。"),
                _condition("element", value=["土"], weight=0.8, evidence_text="土象对应家庭承载和现实责任。"),
            ]
        if event_type in {"family_asset_discussion", "household_repair"}:
            return [
                _condition("is_wealth_month", evidence_text=f"{scene}会牵涉资产、费用或现实支出。"),
                _condition("is_resource_month", evidence_text=f"{scene}和房屋、家庭保护、长辈意见有关。"),
                _condition("clash_year_branch", weight=1.1, evidence_text="年支代表家庭资产和家族事务。"),
                _condition("element", value=["土", "金"], weight=0.8, evidence_text="土看房屋资产，金看家电设备和规则边界。"),
                _condition("group_count_at_least", value=[{"group": "wealth", "min": 1}], weight=0.8, evidence_text="财星参与时更容易落到费用和资产安排。"),
            ]
        return [
            _condition("is_resource_month", evidence_text=f"{scene}和长辈、家庭照应、安顿保护有关。"),
            _condition("clash_year_branch", weight=1.1, evidence_text="年支代表长辈和家庭背景，被冲动时家中事务更明显。"),
            _condition("element", value=["土", "木"], weight=0.8, evidence_text="土看家庭责任，木看长辈状态和成长照应。"),
            _condition("group_count_at_least", value=[{"group": "resource", "min": 1}], weight=0.8, evidence_text="印星可见，家庭和长辈议题更容易出现。"),
        ]
    if group == "risk":
        if event_type in {"rule_penalty", "document_missing"}:
            return [
                _condition("is_officer_month", evidence_text=f"{scene}和规则、流程、处罚或审批有关。"),
                _condition("is_resource_month", evidence_text=f"{scene}和文书、资料、凭证有关。"),
                _condition("favorable_relation", value=["忌神相关"], weight=1.0, evidence_text="忌神参与时更适合作风险降级提醒。"),
                _condition("clash_any", weight=1.0, evidence_text="冲动容易带来遗漏、退回或规则摩擦。"),
                _condition("element", value=["金", "土"], weight=0.8, evidence_text="金主规则边界，土主材料流程。"),
            ]
        if event_type in {"misunderstanding_risk", "overcommitment", "impulsive_decision"}:
            return [
                _condition("is_output_month", evidence_text=f"{scene}和表达、承诺、沟通反应有关。"),
                _condition("is_peer_month", evidence_text=f"{scene}可能牵涉朋友同事或同辈影响。"),
                _condition("favorable_relation", value=["忌神相关"], weight=1.0, evidence_text="忌神参与时更容易放大误判和情绪反应。"),
                _condition("clash_any", weight=1.0, evidence_text="冲动信号让变动和误会概率上升。"),
                _condition("element", value=["火"], weight=0.8, evidence_text="火象对应急躁、表达和情绪上头。"),
            ]
        return [
            _condition("is_wealth_month", evidence_text=f"{scene}容易落到费用、损耗或现实成本。"),
            _condition("is_officer_month", evidence_text=f"{scene}可能与规则、责任或设备流程有关。"),
            _condition("favorable_relation", value=["忌神相关"], weight=1.0, evidence_text="忌神参与时不宜放大行动。"),
            _condition("clash_any", weight=1.0, evidence_text="冲动原局地支时，现实损耗更要提前检查。"),
            _condition("element", value=["金", "土", "火"], weight=0.8, evidence_text="金看设备规则，土看成本资料，火看急躁操作。"),
        ]
    if group == "traffic":
        return [
            _condition("clash_any", weight=1.1, evidence_text=f"{scene}通常和移动、变动或路线调整有关。"),
            _condition("is_officer_month", evidence_text="官杀月对应规则、安全边界和交通约束。"),
            _condition("is_wealth_month", evidence_text="财星月容易对应车辆费用、票据和出行成本。"),
            _condition("element", value=["金", "水", "火"], weight=0.8, evidence_text="金看车辆工具，水看流动路线，火看速度急躁。"),
            _condition("month_index", value=[2, 5, 8, 11], weight=0.6, evidence_text="阶段性出行、差旅或手续确认更容易浮现。"),
        ]
    if group == "housing":
        return [
            _condition("is_resource_month", evidence_text=f"{scene}和房屋、居住、保护和稳定空间有关。"),
            _condition("is_wealth_month", evidence_text=f"{scene}可能牵涉资产、租金、押金或维修支出。"),
            _condition("element", value=["土", "金"], weight=0.9, evidence_text="土看房屋空间，金看家电、合同和结构。"),
            _condition("branch_in", value=["辰", "戌", "丑", "未"], weight=0.8, evidence_text="土库月更容易触发房屋、装修和居住环境。"),
            _condition("clash_day_branch", weight=0.8, evidence_text="日支代表居住状态和一对一租约关系。"),
        ]
    return [
        _condition("is_peer_month", evidence_text=f"{EVENT_DETAILS[event_type]['scene']}和朋友同辈、人情圈层有关。"),
        _condition("is_output_month", evidence_text="食伤月对应表达、饭局、传播和口舌沟通。"),
        _condition("activate_peach_blossom", weight=1.0, evidence_text="人缘象被引动，聚会、评价和旧关系更容易出现。"),
        _condition("element", value=["火", "水"], weight=0.8, evidence_text="火看热闹曝光，水看流动联系。"),
        _condition("group_count_at_least", value=[{"group": "peer", "min": 1}], weight=0.8, evidence_text="比劫可见，朋友同辈和圈层互动更容易成为主题。"),
    ]


def _chain_fields(event_type: str, label: str, group: str) -> dict[str, Any]:
    detail = EVENT_DETAILS[event_type]
    basis = GROUP_BASIS[group]
    palace = dict(COMMON_PALACE)
    palace["specific_focus"] = [detail["scene"]]
    return {
        "traditional_basis": {
            "ten_god_basis": basis["ten_god"],
            "element_basis": basis["element"],
            "branch_relation_basis": basis["branch"],
            "shensha_basis": [
                "神煞只作为辅助加权，不单独决定事件。",
                "桃花、驿马、天乙贵人等只有在系统可靠实现并与十神/宫位同现时才作为参考。",
            ],
            "source_ids": CORE_SOURCES[:4],
        },
        "structure_basis": {
            "required_patterns": basis["required"],
            "supporting_patterns": [f"{label}对应的现实场景清楚：{detail['scene']}", "流月十神、五行或地支关系至少再命中一项。"],
            "risk_patterns": basis["anti"],
        },
        "palace_basis": palace,
        "modern_mapping": {
            "positive_expression": [detail["positive"], f"{label}相关事项有机会被提前整理。"],
            "neutral_expression": [detail["neutral"], f"{label}信号出现时，建议先确认时间、金额、责任和边界。"],
            "negative_expression": [detail["negative"], f"{label}若伴随忌神或冲动，需要先降级观察。"],
        },
        "confidence_basis": COMMON_CONFIDENCE,
        "anti_triggers": basis["anti"],
        "user_visible_basis": f"{label}不是泛泛提醒，重点看{detail['scene']}是否和流月十神、五行喜忌、宫位变动一起出现。",
        "required_evidence_count": 2,
        "subtype_rules": {
            "正向推进型": [detail["positive"], "喜用相关", "证据来源不少于三类"],
            "中性观察型": [detail["neutral"], "需要现实确认", "不直接放大判断"],
            "风险降级型": [detail["negative"], "忌神或冲动参与", "先做检查和边界确认"],
        },
    }


def _variants(event_type: str, label: str) -> list[dict[str, Any]]:
    detail = EVENT_DETAILS[event_type]
    return [
        {
            "variant_id": f"{event_type}_focus",
            "trigger_pattern": ["喜用", "宫位", "十神"],
            "one_line": f"{label}的信号更具体落在：{detail['scene']}。",
            "real_world_signals": [detail["positive"], detail["neutral"], detail["scene"]],
            "risk_points": [detail["negative"], "别只凭口头信息推进"],
            "advice": f"遇到{label}时，先把时间、金额、责任人和后续成本列清楚，再决定推进节奏。",
        },
        {
            "variant_id": f"{event_type}_risk",
            "trigger_pattern": ["忌神", "冲", "压力"],
            "one_line": f"{label}如果伴随反复或压力，先按风险事项处理，不急着扩大判断。",
            "real_world_signals": [detail["negative"], detail["neutral"]],
            "risk_points": ["临时变动", "边界不清", "后续成本未确认"],
            "advice": f"建议把{label}拆成可核对的小事项，先确认凭证、流程和现实信号。",
        },
    ]


def expand_to_150() -> None:
    ontology = _load("monthly_event_ontology.json")
    trigger_rules = _load("monthly_event_trigger_rules.json")
    variants = _load("monthly_event_variants.json")

    target_to_group = {
        event_type: group
        for group, event_types in EVENT_GROUPS.items()
        for event_type in event_types
    }

    for event_type, group in target_to_group.items():
        if event_type not in ontology:
            continue
        label = ontology[event_type].get("label", event_type)
        ontology[event_type].update(_chain_fields(event_type, label, group))
        ontology[event_type]["source_ids"] = sorted(set(ontology[event_type].get("source_ids", []) + CORE_SOURCES))
        ontology[event_type]["basis"] = f"{label}基于{GROUP_BASIS[group]['required'][0]}，再结合现实场景：{EVENT_DETAILS[event_type]['scene']}。"
        variants[event_type] = _variants(event_type, label)

    for rule in trigger_rules:
        event_type = rule.get("target_event_type")
        group = target_to_group.get(event_type)
        if not group:
            continue
        label = ontology[event_type].get("label", event_type)
        # Keep the legacy safety case active with two concrete signals
        # (officer/killing pressure + branch clash), while preserving the
        # richer condition set for confidence scoring.
        rule["min_trigger_count"] = 2 if event_type == "safety_attention" else 3
        rule["trigger_conditions"] = _conditions_for(event_type, group)
        rule["source_ids"] = CORE_SOURCES
        rule["basis"] = f"{label}不靠单一关键词触发，需同时观察传统十神/五行、宫位地支和现代场景：{EVENT_DETAILS[event_type]['scene']}。"
        rule["confidence"] = "v1.0.4.5 150证据链扩展"

    _save("monthly_event_ontology.json", ontology)
    _save("monthly_event_trigger_rules.json", trigger_rules)
    _save("monthly_event_variants.json", variants)


if __name__ == "__main__":
    expand_to_150()
    print("event evidence-chain coverage expanded to targeted 150+")
