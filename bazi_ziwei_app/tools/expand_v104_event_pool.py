"""Generate v1.0.4 monthly event rule assets.

The generated files are intentionally data-heavy JSON assets. Each event has
at least two trigger conditions and at least two narrative variants.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"

SOURCE_IDS = [
    "yuan_hai_zi_ping",
    "san_ming_tong_hui",
    "ming_li_tan_yuan",
    "yu_zhao_ding_zhen_jing",
    "wu_xing_jing_ji",
]

FORBIDDEN = [
    "必定",
    "绝对",
    "注定",
    "一定发财",
    "一定离婚",
    "必定破财",
    "必有灾",
    "必有大病",
    "短命",
    "一定买房",
    "必有车祸",
]


EVENT_GROUPS = {
    "财务收入": [
        ("client_payment", "客户回款", ["客户尾款确认", "账期推进", "订单结算"]),
        ("project_income", "项目收益", ["项目结算", "阶段奖金", "服务费入账"]),
        ("sales_conversion", "客户成交", ["报价成交", "新客户下单", "销售转化"]),
        ("salary_bonus", "工资奖金", ["绩效奖金", "工资调整", "补贴到账"]),
        ("side_income", "副业收入", ["副业订单", "兼职收益", "小项目收入"]),
        ("resource_monetization", "资源变现", ["资源介绍费", "渠道收益", "存量资源盘活"]),
        ("commission_income", "佣金提成", ["提成确认", "代理佣金", "分销收益"]),
        ("delayed_payment_arrival", "延迟款项到账", ["拖延款到账", "旧账推进", "尾款补齐"]),
        ("refund_rebate", "退款返利", ["退款到账", "返点返利", "优惠补回"]),
        ("asset_appreciation_signal", "资产增值信号", ["资产报价变动", "房车估值关注", "持有资产议价"]),
        ("business_cash_in", "经营现金流进入", ["门店流水", "经营回款", "批量收款"]),
        ("unexpected_income", "临时收入", ["临时红包", "意外订单", "短期收益"]),
        ("wealth_inflow", "进账机会", ["回款进账", "收入确认", "收益落袋"]),
        ("business_surprise", "项目财务转机", ["报价转机", "财务节点推进", "项目突然有反馈"]),
    ],
    "财务支出": [
        ("wealth_outflow", "支出增加", ["预算超支", "计划外花费", "支出项目增多"]),
        ("cashflow_pressure", "现金流压力", ["周转安排", "账期压力", "收支时间错位"]),
        ("cooperation_money", "合伙分账", ["分账谈判", "合作分润", "账目核对"]),
        ("debt_borrowing", "借贷往来", ["借款沟通", "还款安排", "垫付往来"]),
        ("debt_loss", "坏账拖欠", ["欠款拖延", "借出难收", "担保压力"]),
        ("human_cost", "人情破耗", ["人情开销", "请客送礼", "替人处理费用"]),
        ("social_spending", "应酬消费", ["饭局酒局花费", "活动消费", "社交场合支出"]),
        ("investment_risk", "投资谨慎", ["高风险项目", "跟风投资", "短线波动"]),
        ("equipment_purchase", "设备采购", ["办公设备", "生产工具", "电子设备"]),
        ("repair_expense", "维修支出", ["设备维修", "车辆维修", "房屋维修"]),
        ("family_expense", "家庭支出", ["家用支出", "长辈花费", "家庭采购"]),
        ("medical_expense_signal", "体检调养支出", ["体检费用", "调理花费", "药品检查"]),
        ("penalty_fee", "罚款滞纳费用", ["罚单", "滞纳金", "补缴费用"]),
        ("subscription_fee", "服务续费", ["软件续费", "会员续费", "服务年费"]),
    ],
    "事业职场": [
        ("project_progress", "项目推进", ["项目节点推进", "任务落地", "方案执行"]),
        ("project_breakthrough", "项目突破", ["卡点突破", "关键反馈", "进度明显推进"]),
        ("project_delay", "项目延期", ["进度拖延", "等待审批", "资源未到位"]),
        ("work_block", "工作卡点", ["流程堵点", "任务反复", "协作不顺"]),
        ("career_change", "岗位变化", ["职责调整", "岗位变化", "工作方向切换"]),
        ("boss_pressure", "上级压力", ["上级催促", "目标加码", "检查考核"]),
        ("performance_review", "考核评估", ["绩效沟通", "结果复盘", "指标检查"]),
        ("promotion_signal", "升职机会", ["职位机会", "承担更大职责", "被看见"]),
        ("responsibility_increase", "责任增加", ["任务变多", "带人带项目", "关键责任落身"]),
        ("team_conflict", "团队摩擦", ["同事分歧", "团队协作卡顿", "责任划分"]),
        ("colleague_support", "同事协助", ["同事搭手", "内部协同", "团队补位"]),
        ("public_expression", "汇报展示", ["汇报演示", "公开表达", "作品呈现"]),
        ("skill_output", "技能输出", ["专业交付", "技术成果", "经验输出"]),
        ("workplace_reputation", "职场评价", ["口碑评价", "上级印象", "同事反馈"]),
        ("resignation_thought", "离职转向念头", ["想换方向", "职业转向", "重新评估岗位"]),
    ],
    "创业经营": [
        ("store_operation", "门店经营", ["门店流水", "客流变化", "店面管理"]),
        ("customer_growth", "客户增长", ["新客户增加", "复购提升", "渠道拓展"]),
        ("customer_complaint", "客户投诉", ["售后沟通", "投诉处理", "客户不满"]),
        ("supplier_issue", "供应商问题", ["供货延迟", "质量沟通", "供应商议价"]),
        ("inventory_pressure", "库存压力", ["库存积压", "补货节奏", "周转压力"]),
        ("pricing_adjustment", "价格调整", ["重新报价", "套餐调整", "利润测算"]),
        ("marketing_exposure", "宣传曝光", ["活动推广", "品牌露出", "广告投放"]),
        ("content_traffic", "内容流量", ["作品播放", "内容反馈", "账号曝光"]),
        ("account_growth", "账号涨粉", ["粉丝增长", "互动增加", "社媒反馈"]),
        ("business_partnership", "商业合作", ["合作洽谈", "资源互换", "联名项目"]),
        ("business_negotiation", "商务谈判", ["报价谈判", "合同谈判", "合作条件"]),
        ("operation_cost", "经营成本上升", ["租金人工", "材料上涨", "运营费用"]),
    ],
    "合同法务": [
        ("contract_document", "合同文书", ["合同条款", "文书确认", "签约准备"]),
        ("approval_process", "审批流程", ["流程审批", "盖章签字", "内部流转"]),
        ("legal_compliance", "规则合规", ["合规检查", "制度要求", "监管规则"]),
        ("official_dispute", "投诉争议", ["投诉沟通", "争议处理", "口舌是非"]),
        ("license_document", "证照手续", ["证件办理", "执照手续", "资质材料"]),
        ("document_error", "材料遗漏", ["资料缺项", "填写错误", "反复补件"]),
        ("policy_change", "规则变化", ["政策调整", "制度更新", "流程变化"]),
        ("tax_invoice", "发票税务", ["开票报税", "发票核对", "税务资料"]),
        ("insurance_claim", "保险理赔", ["理赔材料", "保险沟通", "赔付确认"]),
        ("dispute_mediation", "争议协调", ["中间协调", "协商解决", "调解沟通"]),
    ],
    "房产居住": [
        ("property_housing", "房产居住", ["房屋安排", "居住事务", "房产沟通"]),
        ("asset_purchase", "大件资产购买", ["房车大件", "设备添置", "资产采购"]),
        ("house_viewing", "看房", ["看房比较", "房源筛选", "价格咨询"]),
        ("rental_move", "租房搬迁", ["搬家租房", "换住处", "租约调整"]),
        ("renovation_equipment", "装修设备", ["装修计划", "设备配置", "空间改造"]),
        ("home_repair", "家中维修", ["水电维修", "家具家电", "小修小补"]),
        ("appliance_issue", "家电设备问题", ["家电故障", "设备更换", "维修预约"]),
        ("shop_property", "店铺门面", ["店面选址", "门面租约", "经营场地"]),
        ("family_asset", "家庭资产", ["家庭房产", "共同资产", "资产商议"]),
        ("landlord_tenant", "房东租客", ["租金沟通", "房东租客", "押金合同"]),
        ("property_contract", "房屋合同", ["买卖合同", "租赁合同", "产权资料"]),
        ("living_environment_change", "居住环境变化", ["换环境", "邻里物业", "空间调整"]),
    ],
    "交通车辆": [
        ("travel_traffic", "通勤出行", ["通勤奔波", "短途出行", "路线调整"]),
        ("travel_delay", "行程延误", ["航班高铁延误", "堵车等待", "计划变动"]),
        ("business_trip", "出差外出", ["出差安排", "外地沟通", "短期奔波"]),
        ("vehicle_safety", "驾驶安全提醒", ["开车慢一点", "车况检查", "避免赶路"]),
        ("safety_attention", "操作交通安全", ["工具使用", "路上留神", "避免急躁"]),
        ("vehicle_expense", "车辆支出", ["油费停车", "保养费用", "交通成本"]),
        ("vehicle_repair", "车辆维修", ["车辆保养", "维修检查", "轮胎电瓶"]),
        ("traffic_ticket", "罚单违章", ["违章罚单", "停车罚款", "规则提醒"]),
        ("parking_insurance", "停车保险", ["保险续费", "停车缴费", "车险材料"]),
        ("route_change", "路线变更", ["改路线", "换交通方式", "临时绕行"]),
        ("long_distance_travel", "远行差旅", ["远行安排", "跨城出行", "长途计划"]),
        ("travel_document", "出行证件", ["证件检查", "签证材料", "票据凭证"]),
    ],
    "社交人情": [
        ("social_drinking", "酒局应酬", ["酒局饭局", "朋友邀约", "应酬场合"]),
        ("favor_obligation", "人情往来", ["人情请托", "帮忙协调", "礼尚往来"]),
        ("friend_request", "朋友求助", ["朋友借力", "同辈求助", "帮忙牵线"]),
        ("networking", "资源局", ["资源饭局", "新圈层", "介绍认识"]),
        ("reputation_attention", "名声评价", ["别人评价", "口碑传播", "面子问题"]),
        ("gossip_dispute", "口舌是非", ["闲话误会", "被议论", "沟通争执"]),
        ("gift_expense", "礼物红包", ["红包礼物", "请客送礼", "节日人情"]),
        ("banquet_party", "宴席聚会", ["聚会宴席", "婚宴饭局", "家庭饭局"]),
        ("old_friend_contact", "旧友联系", ["老朋友联系", "旧关系回访", "同学同事消息"]),
        ("social_boundary", "社交边界", ["拒绝请托", "承诺边界", "人情分寸"]),
    ],
    "感情婚恋": [
        ("relationship_progress", "关系推进", ["关系确认", "沟通推进", "相处升温"]),
        ("relationship_conflict", "关系摩擦", ["伴侣争执", "语气误会", "边界拉扯"]),
        ("old_contact", "旧人联系", ["旧人消息", "前任动态", "旧关系回流"]),
        ("peach_blossom_contact", "桃花接触", ["新认识", "暧昧信号", "社交桃花"]),
        ("emotional_distance", "冷淡疏离", ["联系变少", "情绪疏远", "节奏不同"]),
        ("partner_planning", "伴侣规划", ["共同计划", "未来安排", "现实讨论"]),
        ("family_pressure", "家庭介入", ["父母意见", "家庭压力", "亲友参与"]),
        ("misunderstanding", "误会解释", ["解释误会", "沟通澄清", "信息不对称"]),
        ("confession_signal", "表白确认", ["表达心意", "确认关系", "关键对话"]),
        ("breakup_risk_signal", "关系降温信号", ["冷战拉扯", "关系降温", "重新评估"]),
        ("marriage_discussion", "婚姻讨论", ["婚期房车", "结婚安排", "双方家庭"]),
        ("value_conflict", "价值观冲突", ["消费观差异", "生活节奏", "目标不同"]),
        ("long_distance_issue", "异地距离问题", ["异地沟通", "见面不便", "时间错位"]),
        ("cooperation_boundary", "合作边界影响关系", ["合作暧昧", "朋友介入", "边界不清"]),
    ],
    "家庭长辈": [
        ("family_issue", "家庭事务", ["家中安排", "家庭沟通", "旧事处理"]),
        ("elder_issue", "长辈事务", ["长辈沟通", "探望照顾", "长辈安排"]),
        ("family_discussion", "家庭商议", ["家庭会议", "共同决定", "家人沟通"]),
        ("family_asset_discussion", "家庭资产讨论", ["房产资产", "分配商量", "共同出资"]),
        ("household_repair", "家中维修", ["水电维修", "家居处理", "物业问题"]),
        ("sibling_relative_issue", "亲戚兄弟事务", ["亲戚往来", "兄弟姐妹", "家族协调"]),
        ("parent_health_attention", "父母状态关注", ["父母体检", "长辈作息", "陪伴照看"]),
        ("family_responsibility", "家庭责任增加", ["家中责任", "照顾安排", "事务承担"]),
    ],
    "学习证书": [
        ("study_exam", "学习考试", ["考试准备", "课程学习", "复习资料"]),
        ("certificate_training", "证书培训", ["证书报名", "培训课程", "资质提升"]),
        ("skill_upgrade", "技能提升", ["技能练习", "专业进修", "工具学习"]),
        ("writing_output", "写作输出", ["写方案", "文章输出", "资料整理"]),
        ("learning_block", "学习卡点", ["理解卡点", "进度拖慢", "考试焦虑"]),
        ("interview_exam", "面试考核", ["面试准备", "资格审核", "能力测评"]),
        ("knowledge_payment", "知识付费", ["买课程", "咨询付费", "学习投入"]),
        ("teacher_mentor_help", "老师导师帮助", ["导师点拨", "老师建议", "前辈指导"]),
    ],
    "健康状态": [
        ("sleep_issue", "睡眠状态", ["入睡困难", "熬夜恢复", "睡眠质量"]),
        ("emotional_pressure", "情绪压力", ["焦虑烦躁", "压力积累", "情绪波动"]),
        ("digestion_issue", "脾胃消化", ["胃口变化", "消化不适", "饮食不规律"]),
        ("fire_anxiety", "心火焦虑", ["上火焦躁", "心烦睡浅", "急躁感"]),
        ("kidney_fatigue", "腰肾精力", ["腰背疲劳", "精力不足", "恢复变慢"]),
        ("respiratory_skin", "呼吸皮肤", ["皮肤过敏", "呼吸干燥", "鼻咽不适"]),
        ("overwork", "过劳疲劳", ["工作过量", "身体透支", "休息不足"]),
        ("health_fluctuation", "状态波动", ["精神不稳", "疲劳波动", "小问题反复"]),
        ("medical_attention", "体检复查", ["体检安排", "复查项目", "早处理小不适"]),
        ("eye_head_attention", "头眼提醒", ["头眼疲劳", "用眼过度", "头部紧张"]),
        ("shoulder_neck_issue", "肩颈筋骨", ["肩颈酸紧", "筋骨拉扯", "久坐问题"]),
        ("liver_gallbladder_tension", "肝胆疏泄", ["情绪郁结", "肝胆压力", "运动疏泄"]),
        ("dampness_metabolism", "湿气代谢", ["困倦沉重", "代谢慢", "脾胃湿重"]),
        ("recovery_rest", "恢复休养", ["休整恢复", "调养节奏", "减少透支"]),
        ("illness_symbol_attention", "病符小疾提醒", ["小病早看", "体检复查", "炎症上火"]),
    ],
    "贵人与资源": [
        ("nobleman_help", "贵人协助", ["关键帮助", "有人搭桥", "被人提醒"]),
        ("mentor_advice", "前辈建议", ["前辈点拨", "导师建议", "专业意见"]),
        ("resource_connection", "资源连接", ["资源对接", "信息介绍", "渠道连接"]),
        ("referral_opportunity", "转介绍机会", ["客户介绍", "朋友推荐", "机会转介"]),
        ("platform_support", "平台扶持", ["平台资源", "组织支持", "制度保护"]),
        ("team_support", "团队支持", ["团队帮忙", "同事支援", "共同推进"]),
        ("family_support", "家庭支持", ["家人支持", "家庭资源", "情绪依靠"]),
        ("hidden_help", "暗中帮助", ["背后支持", "隐性资源", "有人照应"]),
    ],
    "风险损耗": [
        ("minor_loss", "小额损耗", ["丢小物", "小额花费", "反复补钱"]),
        ("delayed_issue", "拖延滞后", ["进度拖慢", "等待回复", "反复确认"]),
        ("misunderstanding_risk", "误会风险", ["沟通误差", "表达被误解", "信息错位"]),
        ("rule_penalty", "规则处罚", ["罚单处罚", "流程违规", "制度提醒"]),
        ("impulsive_decision", "冲动决策", ["一时冲动", "未经核算", "情绪化决定"]),
        ("overcommitment", "承诺过多", ["答应太多", "责任超量", "时间排满"]),
        ("hidden_cost", "隐藏成本", ["附加费用", "后续成本", "看不见的消耗"]),
        ("emotional_spending", "情绪消费", ["心情消费", "冲动下单", "补偿式花钱"]),
        ("equipment_fault", "设备故障", ["电脑手机", "工具故障", "设备掉链子"]),
        ("document_missing", "资料遗漏", ["漏材料", "忘带证件", "信息缺项"]),
    ],
}


CATEGORY_RULES = {
    "财务收入": {
        "base": [{"type": "is_wealth_month"}, {"type": "is_output_month"}, {"type": "favorable_relation", "value": ["喜用相关"]}],
        "elements": ["土", "金", "水"],
        "groups": ["wealth", "output"],
        "basis": "财星、食伤与喜用五行共同引动时，收入、回款和资源变现类事项更容易浮现。",
    },
    "财务支出": {
        "base": [{"type": "is_peer_month"}, {"type": "is_wealth_month"}, {"type": "favorable_relation", "value": ["忌神相关"]}, {"type": "clash_any"}],
        "elements": ["土", "金"],
        "groups": ["peer", "wealth"],
        "basis": "比劫、财星、忌神或冲动叠加时，现实中更容易表现为分账、人情和计划外支出。",
    },
    "事业职场": {
        "base": [{"type": "is_officer_month"}, {"type": "is_output_month"}, {"type": "clash_month_branch"}],
        "elements": ["金", "火", "土"],
        "groups": ["officer", "output"],
        "basis": "官杀主规则责任，食伤主表达交付，月支主工作环境，叠加后容易落到职场事件。",
    },
    "创业经营": {
        "base": [{"type": "is_wealth_month"}, {"type": "is_output_month"}, {"type": "favorable_relation", "value": ["喜用相关"]}],
        "elements": ["火", "土", "金"],
        "groups": ["wealth", "output"],
        "basis": "财星代表经营流转，食伤代表产品和表达，喜用参与时更适合转为经营动作。",
    },
    "合同法务": {
        "base": [{"type": "is_officer_month"}, {"type": "ten_god", "value": ["伤官"]}, {"type": "element", "value": ["金"]}, {"type": "clash_month_branch"}],
        "elements": ["金", "水"],
        "groups": ["officer", "output"],
        "basis": "官杀与金象对应规则、流程、合同，伤官参与时需把口头表达落到文字。",
    },
    "房产居住": {
        "base": [{"type": "is_resource_month"}, {"type": "is_wealth_month"}, {"type": "element", "value": ["土"]}, {"type": "clash_day_branch"}],
        "elements": ["土"],
        "groups": ["resource", "wealth"],
        "basis": "土象、印星与财星共同引动时，常对应房屋、店铺、设备和居住承载事务。",
    },
    "交通车辆": {
        "base": [{"type": "clash_any"}, {"type": "is_officer_month"}, {"type": "ten_god", "value": ["七杀", "偏财"]}, {"type": "element", "value": ["火", "金", "水"]}],
        "elements": ["火", "金", "水"],
        "groups": ["officer", "wealth"],
        "basis": "冲动、七杀、偏财和火金水取象叠加时，更适合提醒车辆、出行和工具安全。",
    },
    "社交人情": {
        "base": [{"type": "is_peer_month"}, {"type": "activate_peach_blossom"}, {"type": "clash_day_branch"}],
        "elements": ["火", "水"],
        "groups": ["peer"],
        "basis": "比劫主同辈朋友，桃花与日支引动时，人情往来、饭局和口舌更容易出现。",
    },
    "感情婚恋": {
        "base": [{"type": "activate_spouse_palace"}, {"type": "activate_peach_blossom"}, {"type": "is_wealth_month"}, {"type": "is_officer_month"}],
        "elements": ["水", "火", "木"],
        "groups": ["wealth", "officer", "output"],
        "basis": "夫妻宫、桃花、财官关系星被引动时，关系推进或关系压力更容易被看见。",
    },
    "家庭长辈": {
        "base": [{"type": "clash_year_branch"}, {"type": "is_resource_month"}, {"type": "element", "value": ["土"]}],
        "elements": ["土", "木"],
        "groups": ["resource", "wealth"],
        "basis": "年支对应家庭背景与长辈，印星和土象主承载，被流月带动时容易转为家庭事务。",
    },
    "学习证书": {
        "base": [{"type": "is_resource_month"}, {"type": "is_output_month"}, {"type": "favorable_relation", "value": ["喜用相关"]}],
        "elements": ["木", "水"],
        "groups": ["resource", "output"],
        "basis": "印星主学习系统，食伤主输出表达，喜用参与时更适合学习、考试和技能提升。",
    },
    "健康状态": {
        "base": [{"type": "favorable_relation", "value": ["忌神相关"]}, {"type": "is_officer_month"}, {"type": "clash_any"}, {"type": "element_strength", "value": ["overstrong", "weak"]}],
        "elements": ["木", "火", "土", "金", "水"],
        "groups": ["officer", "resource"],
        "basis": "忌神、冲动、官杀压力和五行偏旺偏弱叠加时，只做身体状态管理提醒，不作医学判断。",
    },
    "贵人与资源": {
        "base": [{"type": "is_resource_month"}, {"type": "favorable_relation", "value": ["喜用相关"]}, {"type": "group_count_at_least", "value": [{"group": "resource", "min": 2}]}],
        "elements": ["木", "水", "土"],
        "groups": ["resource"],
        "basis": "印星、喜用和原局资源星共同出现时，更容易对应帮助、平台、导师和转介绍。",
    },
    "风险损耗": {
        "base": [{"type": "favorable_relation", "value": ["忌神相关"]}, {"type": "clash_any"}, {"type": "is_peer_month"}, {"type": "is_officer_month"}],
        "elements": ["金", "火", "土"],
        "groups": ["peer", "officer"],
        "basis": "忌神、冲动、比劫和官杀叠加时，更适合提示损耗、延误、规则和误会风险。",
    },
}


def _source_ids_for_category(category: str) -> list[str]:
    if category in {"交通车辆", "社交人情", "风险损耗"}:
        return ["yuan_hai_zi_ping", "ming_li_tan_yuan", "yu_zhao_ding_zhen_jing", "wu_xing_jing_ji"]
    if category in {"健康状态", "房产居住"}:
        return ["san_ming_tong_hui", "qiong_tong_bao_jian", "ming_li_tan_yuan", "wu_xing_jing_ji"]
    return SOURCE_IDS


def _condition_with_sources(cond: dict, source_ids: list[str], event_type: str) -> dict:
    item = dict(cond)
    item.setdefault("weight", 1)
    item.setdefault("evidence_text", f"{event_type} 触发条件")
    item["source_ids"] = source_ids[:3]
    return item


def _month_condition(index: int) -> dict:
    first = (index % 12) + 1
    second = ((index + 4) % 12) + 1
    return {"type": "month_index", "value": [first, second], "weight": 0.8, "evidence_text": "流月序位与事件节奏匹配"}


def _build_rule(event_type: str, category: str, index: int, source_ids: list[str]) -> dict:
    spec = CATEGORY_RULES[category]
    conditions = list(spec["base"])
    special_conditions = {
        "cooperation_money": [{"type": "ten_god", "value": ["劫财", "比肩"], "weight": 1, "evidence_text": "比劫月触发合伙分账"}],
        "wealth_outflow": [{"type": "ten_god", "value": ["劫财", "比肩"], "weight": 1, "evidence_text": "比劫月触发支出增加"}],
        "digestion_issue": [{"type": "is_output_month", "weight": 1, "evidence_text": "食伤泄身触发脾胃消化"}, {"type": "element", "value": ["土"], "weight": 1, "evidence_text": "土象触发脾胃取象"}],
        "kidney_fatigue": [{"type": "ten_god", "value": ["七杀"], "weight": 1, "evidence_text": "七杀压力触发腰肾精力"}, {"type": "element", "value": ["水"], "weight": 1, "evidence_text": "水象触发腰肾取象"}],
        "legal_compliance": [{"type": "is_officer_month", "weight": 1, "evidence_text": "官杀月触发规则合规"}, {"type": "ten_god", "value": ["七杀", "正官"], "weight": 1, "evidence_text": "官杀十神触发制度压力"}],
        "overwork": [{"type": "is_officer_month", "weight": 1, "evidence_text": "官杀压力触发过劳"}, {"type": "ten_god", "value": ["七杀"], "weight": 1, "evidence_text": "七杀月任务压力增强"}],
        "safety_attention": [{"type": "ten_god", "value": ["七杀"], "weight": 1, "evidence_text": "七杀月触发安全提醒"}, {"type": "clash_any", "weight": 1, "evidence_text": "地支冲动触发安全注意"}],
        "travel_traffic": [{"type": "ten_god", "value": ["七杀", "偏财"], "weight": 1, "evidence_text": "七杀偏财触发动象出行"}, {"type": "clash_any", "weight": 1, "evidence_text": "地支冲动触发通勤出行"}],
        "vehicle_expense": [{"type": "is_wealth_month", "weight": 1, "evidence_text": "财星月触发车辆支出"}, {"type": "ten_god", "value": ["偏财"], "weight": 1, "evidence_text": "偏财月触发交通成本"}],
    }
    conditions.extend(special_conditions.get(event_type, []))
    elements = spec["elements"]
    if elements:
        conditions.append({"type": "element", "value": [elements[index % len(elements)]], "weight": 0.8, "evidence_text": "流月五行取象匹配"})
    groups = spec["groups"]
    if groups:
        conditions.append({"type": "group_count_at_least", "value": [{"group": groups[index % len(groups)], "min": 2}], "weight": 0.8, "evidence_text": "原局对应十神组不弱"})
    conditions.append(_month_condition(index))
    return {
        "rule_id": f"rule_v104_{event_type}",
        "target_event_type": event_type,
        "min_trigger_count": 2,
        "trigger_conditions": [_condition_with_sources(c, source_ids, event_type) for c in conditions],
        "source_ids": source_ids,
        "basis": spec["basis"],
        "confidence": "规则库扩容",
    }


def _ontology_item(event_type: str, label: str, category: str, forms: list[str], source_ids: list[str]) -> dict:
    basis = CATEGORY_RULES[category]["basis"]
    return {
        "event_type": event_type,
        "label": label,
        "category": category,
        "description": f"当流月十神、喜忌、原局结构或地支关系至少两项共同指向时，可关注{label}类现实事项。",
        "possible_real_world_forms": forms,
        "trigger_rules": [f"rule_v104_{event_type}"],
        "evidence_template": "触发因素：{evidence}。现实观察：{forms}。",
        "variants": [f"{event_type}_focus", f"{event_type}_risk"],
        "risk_points": ["节奏过快", "信息不完整", "口头承诺不落文字"],
        "safe_expression": f"本月较容易出现{label}相关信号，建议结合现实安排提前准备。",
        "forbidden_expression": FORBIDDEN,
        "default_probability_level": "需观察",
        "source_ids": source_ids,
        "basis": basis,
    }


def _variants(event_type: str, label: str, category: str, forms: list[str]) -> list[dict]:
    return [
        {
            "variant_id": f"{event_type}_focus",
            "trigger_pattern": ["喜用", "十神", "匹配"],
            "one_line": f"{label}的信号被点亮，重点看{forms[0]}、{forms[1]}这类具体事项。",
            "real_world_signals": forms,
            "risk_points": ["别只听口头反馈", "关键事项留记录"],
            "advice": f"建议把{label}拆成可执行清单，先确认时间、金额、责任人和后续成本。",
        },
        {
            "variant_id": f"{event_type}_risk",
            "trigger_pattern": ["忌神", "冲", "压力"],
            "one_line": f"{label}容易伴随反复或额外消耗，处理时宜慢一点、细一点。",
            "real_world_signals": list(reversed(forms)),
            "risk_points": ["临时变动", "沟通误差", "成本超出预期"],
            "advice": f"遇到{label}相关事项时，先核对凭证和边界，再决定是否推进。",
        },
    ]


def _specific_rule(event_type: str, label: str, category: str, forms: list[str], source_ids: list[str]) -> dict:
    return {
        "event_type": event_type,
        "specific_label": label,
        "trigger_profile": {
            "min_trigger_count": 2,
            "required_evidence": ["流月十神", "五行喜忌", "原局结构或地支关系"],
        },
        "evidence_template": f"{label}由流月十神、喜忌和命盘结构共同触发，不以单一符号下结论。",
        "real_world_template": f"现实中可观察：{'、'.join(forms[:3])}。",
        "risk_template": "需要注意节奏、凭证和边界，不宜凭情绪或口头承诺推进。",
        "advice_template": f"建议围绕{label}提前列清单、留凭证、设缓冲。",
        "source_ids": source_ids,
        "basis": CATEGORY_RULES[category]["basis"],
    }


def main() -> None:
    ontology = {}
    trigger_rules = []
    variants = {}
    specific_rules = []

    index = 0
    for category, events in EVENT_GROUPS.items():
        for event_type, label, forms in events:
            source_ids = _source_ids_for_category(category)
            ontology[event_type] = _ontology_item(event_type, label, category, forms, source_ids)
            trigger_rules.append(_build_rule(event_type, category, index, source_ids))
            variants[event_type] = _variants(event_type, label, category, forms)
            specific_rules.append(_specific_rule(event_type, label, category, forms, source_ids))
            index += 1

    files = {
        "monthly_event_ontology.json": ontology,
        "monthly_event_trigger_rules.json": trigger_rules,
        "monthly_event_variants.json": variants,
        "monthly_specific_event_rules.json": specific_rules,
    }
    for filename, data in files.items():
        (RULES / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    life_pool = {
        "wealth": ["稳定工资型", "项目回款型", "资源变现型", "销售成交型", "投资波动型", "合伙分账型", "技术输出型", "内容流量型", "经营现金流型", "家庭资产型", "人情破耗型", "现金流压力型"],
        "romance": ["稳定陪伴型", "桃花社交型", "旧人回流型", "慢热观察型", "家庭介入型", "合作生情型", "关系摩擦型", "价值观磨合型", "远距离/节奏差型", "婚姻规划型"],
        "health": ["睡眠恢复型", "脾胃消化型", "情绪压力型", "肝胆筋骨型", "呼吸皮肤型", "腰肾精力型", "过劳疲劳型", "湿气代谢型", "心火焦虑型", "体检复查型"],
        "career": ["职场晋升型", "项目突破型", "技术专业型", "内容表达型", "管理责任型", "创业经营型", "客户销售型", "合同文书型", "资源整合型", "学习转型型", "团队协作型", "独立发展型"],
    }
    archetype_rules = []
    for dimension, names in life_pool.items():
        for idx, name in enumerate(names):
            archetype_rules.append({
                "id": f"{dimension}_{idx+1:02d}",
                "title": name,
                "dimension": dimension,
                "condition": {"min_evidence_count": 2, "driven_by": ["日主强弱", "十神分布", "五行喜忌", "宫位/地支关系"]},
                "text": f"{name}需要结合命盘指纹判断，不以单一十神或单一五行直接下结论。",
                "advice": "用作命局总论的差异化类型标签，输出时必须附带命盘依据和现实建议。",
                "source_ids": SOURCE_IDS,
            })
    (RULES / "life_overview_event_pool.json").write_text(
        json.dumps(life_pool, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (RULES / "life_overview_archetype_rules.json").write_text(
        json.dumps(archetype_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"events={len(ontology)} variants={sum(len(v) for v in variants.values())} trigger_rules={len(trigger_rules)} categories={len(EVENT_GROUPS)}")


if __name__ == "__main__":
    main()
