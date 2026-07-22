"""Refine high-similarity finance income event trigger chains.

This keeps the event count unchanged and only differentiates six income events
that previously shared nearly identical trigger rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"

CORE_SOURCE_IDS = [
    "yuan_hai_zi_ping",
    "san_ming_tong_hui",
    "ming_li_tan_yuan",
    "yu_zhao_ding_zhen_jing",
    "wu_xing_jing_ji",
]


def _condition(
    ctype: str,
    *,
    value: Any | None = None,
    weight: float = 1,
    evidence_text: str,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "type": ctype,
        "weight": weight,
        "evidence_text": evidence_text,
        "source_ids": CORE_SOURCE_IDS[:3],
    }
    if value is not None:
        item["value"] = value
    return item


REFINED_RULES: dict[str, dict[str, Any]] = {
    "client_payment": {
        "min_trigger_count": 3,
        "basis": "客户回款重点看财星、合作方/日支、土象账期与凭证流程是否同时被引动，偏向已发生业务的尾款或旧账推进。",
        "conditions": [
            _condition("is_wealth_month", evidence_text="流月财星引动钱款、客户与结算事项。"),
            _condition("clash_day_branch", weight=1.1, evidence_text="日支代表一对一合作方，被冲动时容易出现账期、尾款或结算沟通。"),
            _condition("element", value=["土"], weight=0.9, evidence_text="土象取账册、凭证、承载和实际落袋。"),
            _condition("branch_in", value=["辰", "戌", "丑", "未"], weight=0.9, evidence_text="土库月更容易触发账目归集、库存结算或尾款核对。"),
            _condition("group_count_at_least", value=[{"group": "wealth", "min": 2}], weight=0.8, evidence_text="原局财星不弱，钱款事项更容易成为现实主题。"),
            _condition("favorable_relation", value=["喜用相关"], weight=0.8, evidence_text="喜用参与时，回款推进的顺畅度更高。"),
        ],
    },
    "sales_conversion": {
        "min_trigger_count": 3,
        "basis": "客户成交重点看食伤表达、桃花人缘、报价沟通和客户入口，不等同于已完成回款。",
        "conditions": [
            _condition("is_output_month", evidence_text="食伤月利于表达、展示、报价和销售话术输出。"),
            _condition("activate_peach_blossom", weight=1.1, evidence_text="人缘象被引动，客户接触、询盘和转介绍更容易增加。"),
            _condition("branch_in", value=["子", "午", "卯", "酉"], weight=0.9, evidence_text="桃花地支对应曝光、人际吸引和沟通入口。"),
            _condition("group_count_at_least", value=[{"group": "output", "min": 2}], weight=0.8, evidence_text="原局食伤不弱，能把产品、观点或服务说清楚。"),
            _condition("group_count_at_least", value=[{"group": "wealth", "min": 1}], weight=0.8, evidence_text="财星有根，表达之后更容易接到订单或客户反馈。"),
            _condition("month_index", value=[3, 7, 11], weight=0.6, evidence_text="流月节奏偏向新客户接触、报价反馈或成交确认。"),
        ],
    },
    "salary_bonus": {
        "min_trigger_count": 3,
        "basis": "工资奖金重点看官杀考核、印星制度文书、月支事业环境和组织发放规则，偏向单位内的绩效、补贴或薪资调整。",
        "conditions": [
            _condition("is_officer_month", evidence_text="官杀月引动职位、考核、规则和上级评价。"),
            _condition("is_resource_month", evidence_text="印星月引动制度、文书、审批和组织保护。"),
            _condition("clash_month_branch", weight=1.1, evidence_text="月支代表事业平台，被冲动时容易出现岗位、绩效或薪酬规则变化。"),
            _condition("group_count_at_least", value=[{"group": "officer", "min": 1}], weight=0.8, evidence_text="原局官杀可见，收入更容易和责任、考核、职位挂钩。"),
            _condition("group_count_at_least", value=[{"group": "resource", "min": 1}], weight=0.8, evidence_text="印星可见，补贴、资质、文书流程更容易影响发放。"),
            _condition("favorable_relation", value=["喜用相关", "平稳观察"], weight=0.7, evidence_text="喜用或平稳月份更适合确认薪资福利。"),
            _condition("month_index", value=[4, 8, 12], weight=0.6, evidence_text="季度或阶段性复盘节点更容易出现奖金、补贴和薪资调整。"),
        ],
    },
    "commission_income": {
        "min_trigger_count": 3,
        "basis": "佣金提成重点看食伤推动销售、财星落实收益、比劫分成边界和阶段业绩确认。",
        "conditions": [
            _condition("is_output_month", evidence_text="食伤月利于销售动作、渠道沟通和业绩展示。"),
            _condition("is_wealth_month", evidence_text="财星月引动订单、提成、分账和收益确认。"),
            _condition("group_count_at_least", value=[{"group": "output", "min": 1}], weight=0.8, evidence_text="原局有输出能力，提成通常来自介绍、销售或服务交付。"),
            _condition("group_count_at_least", value=[{"group": "wealth", "min": 2}], weight=0.8, evidence_text="财星不弱，销售结果更容易转成金额。"),
            _condition("group_count_at_least", value=[{"group": "peer", "min": 1}], weight=0.7, evidence_text="比劫参与时，要特别看分成比例、团队归属和合伙边界。"),
            _condition("month_index", value=[2, 6, 10], weight=0.7, evidence_text="阶段业绩结算、渠道分佣或代理收益容易在这类节奏中浮现。"),
        ],
    },
    "side_income": {
        "min_trigger_count": 3,
        "basis": "副业收入重点看食伤技能输出、时支长期项目/副线成果、日主能力标签和业余交付边界。",
        "conditions": [
            _condition("is_output_month", evidence_text="食伤月适合把技能、内容、作品或服务转成小额收入。"),
            _condition("clash_hour_branch", weight=1.1, evidence_text="时支代表副线项目、长期成果和收尾事项，被引动时副业信号更明显。"),
            _condition("day_master_element", value=["木", "火", "金"], weight=0.7, evidence_text="日主五行取象偏向策划、表达、技术或审美输出时，副业转化更有抓手。"),
            _condition("group_count_at_least", value=[{"group": "output", "min": 2}], weight=0.8, evidence_text="原局食伤较足，具备靠技能、内容或交付换取收入的条件。"),
            _condition("favorable_relation", value=["喜用相关"], weight=0.8, evidence_text="喜用参与时，额外收入更容易落在可持续的小项目上。"),
            _condition("month_index", value=[5, 9], weight=0.6, evidence_text="这类月份更适合观察业余订单、兼职收益或小项目结算。"),
        ],
    },
    "business_cash_in": {
        "min_trigger_count": 3,
        "basis": "经营现金流进入重点看月支主业平台、财星流水、土库归集和门店/经营场景，不等同于单笔客户尾款。",
        "conditions": [
            _condition("is_wealth_month", evidence_text="财星月引动流水、收款、订单和经营收入。"),
            _condition("clash_month_branch", weight=1.1, evidence_text="月支代表主业和经营环境，被冲动时容易出现门店流水、客户批量付款或经营节奏变化。"),
            _condition("branch_in", value=["辰", "戌", "丑", "未"], weight=0.9, evidence_text="土库月偏向库存、账目、门店承载和现金归集。"),
            _condition("element", value=["土", "水"], weight=0.8, evidence_text="土看经营承载，水看流动资金和周转。"),
            _condition("group_count_at_least", value=[{"group": "wealth", "min": 2}], weight=0.8, evidence_text="原局财星不弱，经营收入更容易形成持续流水。"),
            _condition("month_index", value=[3, 6, 9, 12], weight=0.6, evidence_text="阶段性盘账、补货、结算和周转压力更容易浮现。"),
        ],
    },
}


ONTOLOGY_UPDATES: dict[str, dict[str, Any]] = {
    "client_payment": {
        "structure_basis": {
            "required_patterns": ["财星引动", "日支/合作方或土库账期被引动"],
            "supporting_patterns": ["旧订单存在", "尾款节点临近", "凭证合同清楚"],
            "risk_patterns": ["日支受冲导致对方反复", "财星为忌导致回款伴随折扣或成本"],
        },
        "modern_mapping": {
            "positive_expression": ["客户确认尾款", "旧账补齐", "阶段账期推进"],
            "neutral_expression": ["对方给出付款时间但仍需走流程", "金额需要再次核对"],
            "negative_expression": ["尾款拖延", "合作方临时改口", "到账前又出现补资料要求"],
        },
        "user_visible_basis": "回款看的是已经发生的业务能不能收尾，重点观察客户尾款、账期、合作方态度和凭证是否齐全。",
        "subtype_rules": {
            "尾款型": ["日支或合作方被引动", "财星出现", "账期临近"],
            "旧账型": ["土库月", "凭证账册", "历史订单"],
            "延迟型": ["日支受冲", "财星为忌", "合同资料反复"],
        },
    },
    "sales_conversion": {
        "structure_basis": {
            "required_patterns": ["食伤表达引动", "桃花/人缘或客户入口被引动"],
            "supporting_patterns": ["报价清晰", "客户询盘增加", "产品服务展示到位"],
            "risk_patterns": ["只热闹不下单", "口头意向多", "价格被反复压低"],
        },
        "modern_mapping": {
            "positive_expression": ["报价后客户确认", "新客户下单", "询盘转成订单"],
            "neutral_expression": ["客户兴趣增加但还在比较", "对方需要再次确认预算"],
            "negative_expression": ["报价被压价", "客户只问不买", "沟通热但成交慢"],
        },
        "user_visible_basis": "成交看的是陌生客户或新需求能不能被说服，重点观察报价、询盘、沟通热度和客户决策速度。",
        "subtype_rules": {
            "新客成交型": ["食伤表达", "桃花人缘", "报价反馈"],
            "转介绍型": ["人缘象", "客户入口", "财星承接"],
            "压价型": ["财星受压", "沟通过度", "客户预算摇摆"],
        },
    },
    "salary_bonus": {
        "structure_basis": {
            "required_patterns": ["官杀考核或印星流程引动", "月支事业环境被引动"],
            "supporting_patterns": ["绩效节点", "上级评价", "制度补贴或薪资调整"],
            "risk_patterns": ["考核压力增加", "审批流程慢", "奖金与责任绑定"],
        },
        "modern_mapping": {
            "positive_expression": ["绩效奖金确认", "补贴到账", "薪资或福利调整"],
            "neutral_expression": ["上级提到奖励但需等审批", "工资结构需要重新确认"],
            "negative_expression": ["奖金延后", "考核压力变大", "补贴条件变多"],
        },
        "user_visible_basis": "工资奖金看的是组织内部规则，重点观察绩效考核、上级评价、补贴审批和薪资结构变化。",
        "subtype_rules": {
            "绩效型": ["官杀考核", "月支事业", "上级评价"],
            "补贴型": ["印星文书", "制度流程", "资格条件"],
            "调薪型": ["岗位责任变化", "薪资结构调整", "组织规则变动"],
        },
    },
    "commission_income": {
        "structure_basis": {
            "required_patterns": ["食伤销售动作", "财星收益承接", "分成边界被引动"],
            "supporting_patterns": ["渠道订单", "业绩确认", "团队或平台结算"],
            "risk_patterns": ["分成比例不清", "归属争议", "回款后才算提成"],
        },
        "modern_mapping": {
            "positive_expression": ["提成确认", "代理佣金入账", "分销收益结算"],
            "neutral_expression": ["业绩已经产生但还要核算比例", "渠道方需要确认归属"],
            "negative_expression": ["分成争议", "提成延迟", "业绩归属被抢"],
        },
        "user_visible_basis": "提成看的是销售结果怎么分，重点观察业绩归属、分成比例、渠道结算和团队边界。",
        "subtype_rules": {
            "销售提成型": ["食伤销售", "财星收益", "业绩节点"],
            "渠道分佣型": ["比劫团队", "平台渠道", "分成比例"],
            "归属争议型": ["比劫竞争", "口头约定", "提成延迟"],
        },
    },
    "side_income": {
        "structure_basis": {
            "required_patterns": ["食伤技能输出", "时支副线项目或长期成果被引动"],
            "supporting_patterns": ["业余订单", "内容作品", "小项目交付"],
            "risk_patterns": ["主业副业时间冲突", "交付边界不清", "小钱耗大精力"],
        },
        "modern_mapping": {
            "positive_expression": ["副业订单", "兼职收益", "小项目结算"],
            "neutral_expression": ["有人询问合作但预算不大", "业余时间需要重新分配"],
            "negative_expression": ["副业拖累休息", "交付范围扩大", "小项目回款慢"],
        },
        "user_visible_basis": "副业收入看的是技能或作品能不能在主业之外变现，重点观察业余订单、交付边界和时间成本。",
        "subtype_rules": {
            "技能变现型": ["食伤技能", "时支副线", "小项目"],
            "内容输出型": ["作品传播", "客户询问", "额外结算"],
            "耗时型": ["交付扩大", "休息被占", "回款慢"],
        },
    },
    "business_cash_in": {
        "structure_basis": {
            "required_patterns": ["财星流水引动", "月支经营环境或土库账目被引动"],
            "supporting_patterns": ["门店流水", "经营回款", "批量收款或库存周转"],
            "risk_patterns": ["流水增加但利润未必增加", "库存补货占用资金", "经营成本同步上升"],
        },
        "modern_mapping": {
            "positive_expression": ["门店流水增加", "批量收款", "经营回款进入"],
            "neutral_expression": ["现金流变活但还要看成本", "销售额增加但利润需要核算"],
            "negative_expression": ["流水进来又被库存占用", "周转压力仍在", "经营成本同步上升"],
        },
        "user_visible_basis": "经营现金流看的是生意整体周转，重点观察门店流水、批量收款、库存补货和经营成本。",
        "subtype_rules": {
            "门店流水型": ["月支经营", "财星流水", "土库承载"],
            "周转型": ["水象流动", "库存补货", "阶段盘账"],
            "成本同步型": ["经营成本", "补货压力", "利润核算"],
        },
    },
}


VARIANT_UPDATES: dict[str, list[dict[str, Any]]] = {
    "client_payment": [
        {
            "variant_id": "client_payment_tail_payment",
            "trigger_pattern": ["日支", "土库", "账期"],
            "one_line": "客户回款更像是尾款、旧账或阶段结算被重新推到台前。",
            "real_world_signals": ["尾款确认", "旧账补齐", "账期推进"],
            "risk_points": ["合作方改口", "凭证不齐", "到账时间再拖"],
            "advice": "先核对合同、发票、交付记录和付款节点，再催对方给出明确日期。",
        },
        {
            "variant_id": "client_payment_delay",
            "trigger_pattern": ["冲", "忌神", "合作方"],
            "one_line": "回款有机会推进，但容易伴随对方流程、资料或金额口径反复。",
            "real_world_signals": ["补资料", "重新核账", "付款时间改期"],
            "risk_points": ["只听口头承诺", "金额未确认", "责任人不清"],
            "advice": "把金额、责任人、付款方式和最晚时间写下来，减少反复沟通。",
        },
    ],
    "sales_conversion": [
        {
            "variant_id": "sales_conversion_new_client",
            "trigger_pattern": ["食伤", "桃花", "报价"],
            "one_line": "成交信号更偏向新客户询盘、报价反馈或转介绍后的下单。",
            "real_world_signals": ["新客户下单", "报价被接受", "询盘转订单"],
            "risk_points": ["客户压价", "只问不买", "需求变来变去"],
            "advice": "把卖点、价格、交付范围讲清楚，先锁定小单或定金比空谈更稳。",
        },
        {
            "variant_id": "sales_conversion_followup",
            "trigger_pattern": ["人缘", "沟通", "客户"],
            "one_line": "客户兴趣度容易上升，但成交需要靠跟进节奏和报价边界来推动。",
            "real_world_signals": ["客户再次咨询", "要求改报价", "试探合作条件"],
            "risk_points": ["让利过多", "承诺太满", "跟进太急"],
            "advice": "用清单式报价，把可让步和不能让步的部分先分开。",
        },
    ],
    "salary_bonus": [
        {
            "variant_id": "salary_bonus_performance",
            "trigger_pattern": ["官杀", "考核", "月支"],
            "one_line": "工资奖金更像是绩效、补贴或岗位责任变化带来的收入调整。",
            "real_world_signals": ["绩效奖金", "补贴到账", "调薪讨论"],
            "risk_points": ["责任增加", "审批慢", "考核压力同步上升"],
            "advice": "主动整理成果和数据，让上级更容易看到你的贡献。",
        },
        {
            "variant_id": "salary_bonus_process",
            "trigger_pattern": ["印星", "审批", "制度"],
            "one_line": "奖金或补贴可能卡在制度、材料或审批节点，需要按流程推进。",
            "real_world_signals": ["资料补交", "审批排队", "福利政策调整"],
            "risk_points": ["材料遗漏", "时间延后", "口径变化"],
            "advice": "把发放条件、材料清单和审批时间问清楚，不要只等通知。",
        },
    ],
    "commission_income": [
        {
            "variant_id": "commission_income_sales_split",
            "trigger_pattern": ["食伤", "销售", "财星"],
            "one_line": "佣金提成更偏向销售结果、渠道订单或服务转化后的分成确认。",
            "real_world_signals": ["提成确认", "代理佣金", "业绩结算"],
            "risk_points": ["比例不清", "归属争议", "平台结算慢"],
            "advice": "先把提成比例、计算口径和到账条件写清楚，避免事后扯皮。",
        },
        {
            "variant_id": "commission_income_team_boundary",
            "trigger_pattern": ["比劫", "分成", "团队"],
            "one_line": "提成可能牵涉团队协作或合伙分成，重点在边界和归属。",
            "real_world_signals": ["团队分账", "渠道归属确认", "业绩被拆分"],
            "risk_points": ["朋友同事介入", "口头约定", "谁贡献更大说不清"],
            "advice": "涉及多人贡献时，尽量提前确认归属和分账规则。",
        },
    ],
    "side_income": [
        {
            "variant_id": "side_income_skill_order",
            "trigger_pattern": ["时支", "食伤", "技能"],
            "one_line": "副业收入更像是技能、内容或小项目在主业之外产生回报。",
            "real_world_signals": ["副业订单", "兼职收益", "小项目结算"],
            "risk_points": ["交付范围扩大", "时间被占", "小钱耗精力"],
            "advice": "先限定交付范围和时间成本，别让副业反过来拖累主业和休息。",
        },
        {
            "variant_id": "side_income_small_project",
            "trigger_pattern": ["额外", "业余", "项目"],
            "one_line": "会有人询问额外合作或小单，但不宜一上来就承诺太多。",
            "real_world_signals": ["朋友介绍小单", "业余咨询", "内容变现"],
            "risk_points": ["预算不大", "需求不清", "回款慢"],
            "advice": "小项目先收定金或明确阶段交付，避免用大项目精力做小项目。",
        },
    ],
    "business_cash_in": [
        {
            "variant_id": "business_cash_in_turnover",
            "trigger_pattern": ["月支", "土库", "流水"],
            "one_line": "经营现金流更像是门店、业务盘子或库存周转带来的批量进账。",
            "real_world_signals": ["门店流水", "批量收款", "经营回款"],
            "risk_points": ["流水不等于利润", "补货占资金", "成本同步增加"],
            "advice": "收入进来后先做利润和现金流拆分，不要只看到账金额。",
        },
        {
            "variant_id": "business_cash_in_cost_balance",
            "trigger_pattern": ["水", "周转", "经营"],
            "one_line": "现金流有流动迹象，但要同时看库存、租金、人力和平台费用。",
            "real_world_signals": ["周转变快", "客户集中付款", "补货付款"],
            "risk_points": ["账面好看但利润薄", "库存压力", "成本后置"],
            "advice": "用一张表分清收入、毛利、固定成本和必须预留的周转金。",
        },
    ],
}


def _load(name: str) -> Any:
    return json.loads((RULES_DIR / name).read_text(encoding="utf-8"))


def _save(name: str, data: Any) -> None:
    (RULES_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refine_rules() -> None:
    trigger_rules = _load("monthly_event_trigger_rules.json")
    ontology = _load("monthly_event_ontology.json")
    variants = _load("monthly_event_variants.json")

    for rule in trigger_rules:
        event_type = rule.get("target_event_type")
        refined = REFINED_RULES.get(event_type)
        if not refined:
            continue
        rule["min_trigger_count"] = refined["min_trigger_count"]
        rule["trigger_conditions"] = refined["conditions"]
        rule["source_ids"] = CORE_SOURCE_IDS
        rule["basis"] = refined["basis"]
        rule["confidence"] = "v1.0.4.4 财务收入触发链差异化"

    for event_type, update in ONTOLOGY_UPDATES.items():
        if event_type not in ontology:
            continue
        ontology[event_type].update(update)
        ontology[event_type]["basis"] = REFINED_RULES[event_type]["basis"]
        ontology[event_type]["source_ids"] = sorted(set(ontology[event_type].get("source_ids", []) + CORE_SOURCE_IDS))

    for event_type, update in VARIANT_UPDATES.items():
        variants[event_type] = update

    _save("monthly_event_trigger_rules.json", trigger_rules)
    _save("monthly_event_ontology.json", ontology)
    _save("monthly_event_variants.json", variants)


if __name__ == "__main__":
    refine_rules()
    print("finance income trigger chains refined")
