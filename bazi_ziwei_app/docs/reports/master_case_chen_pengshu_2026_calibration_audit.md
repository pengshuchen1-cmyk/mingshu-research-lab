# 陈芃澍 2026 流月样本校准审计

本报告用于把现实师傅样本与系统当前 2026 流月 Top3 做逐段对比，先找命中与漏项，再决定调权方向。

## 基础信息
- 样本：陈芃澍
- 年份：2026
- 程序四柱（年/月/日/时）：己卯 壬申 乙未 辛巳
- 纸质盘面四柱按右到左还原：己卯 壬申 乙未 辛巳
- 说明：纸质盘面常见右到左展示；程序按年、月、日、时输出。

## 总体命中
- 六段平均覆盖率：0.904
- 未覆盖事件类型数：3
- 优先漏项：商务谈判(business_negotiation)、小额损耗(minor_loss)、责任增加(responsibility_increase)

## 系统当前 2026 每月 Top3
- 1月 己丑 偏财：项目推进(project_progress)、操作交通安全(safety_attention)、同辈圈层或社交场景带来资源线索(social_resource_cluster)
- 2月 庚寅 正官：投诉争议(official_dispute)、操作交通安全(safety_attention)、同辈圈层或社交场景带来资源线索(social_resource_cluster)
- 3月 辛卯 七杀：合作机会(cooperation_opportunity)、项目突破(project_breakthrough)、关系沟通与外部压力增加(relationship_family_cluster)
- 4月 壬辰 正印：合作机会(cooperation_opportunity)、项目突破(project_breakthrough)、暗中帮助(hidden_help)
- 5月 癸巳 偏印：现实支出压力增加(expense_vehicle_cluster)、被套住(trapped_commitment)、项目财务转机(business_surprise)
- 6月 甲午 劫财：现实支出压力增加(expense_vehicle_cluster)、被套住(trapped_commitment)、人情往来(favor_obligation)
- 7月 乙未 比肩：状态波动(health_fluctuation)、冲动决策(impulsive_decision)、口舌是非(gossip_dispute)
- 8月 丙申 伤官：行程延误(travel_delay)、冲动决策(impulsive_decision)、口舌是非(gossip_dispute)
- 9月 丁酉 食神：情绪压力(emotional_pressure)、关系沟通与外部压力增加(relationship_family_cluster)、客户成交(sales_conversion)
- 10月 戊戌 正财：房产居住(property_housing)、现实支出压力增加(expense_vehicle_cluster)、门店经营(store_operation)
- 11月 己亥 偏财：大件资产购买(asset_purchase)、现实支出压力增加(expense_vehicle_cluster)、情绪压力(emotional_pressure)
- 12月 庚子 正官：投诉争议(official_dispute)、大件资产购买(asset_purchase)、情绪压力(emotional_pressure)

## 六段逐段对比

### 1-2 月
- 师傅原文：注意3号、13号跟23号，注意酒友以及开车，改革要三思，以及有项目。
- 师傅事件映射：酒局应酬(social_drinking)、驾驶安全提醒(vehicle_safety)、操作交通安全(safety_attention)、冲动决策(impulsive_decision)、项目推进(project_progress)、商务谈判(business_negotiation)
- 系统 Top3：项目推进(project_progress)、操作交通安全(safety_attention)、social_resource_cluster(social_resource_cluster)、投诉争议(official_dispute)
- 命中：酒局应酬(social_drinking)、操作交通安全(safety_attention)、项目推进(project_progress)
- 语义命中：驾驶安全提醒(vehicle_safety)、冲动决策(impulsive_decision)
- 漏项：商务谈判(business_negotiation)
- 覆盖率：0.833
- 蒸馏观察：
  - 这一组不是单看财星或单看出行，而是把节点日、酒局场景、车辆安全和项目变动叠在一起看。
  - 系统后续校准时，应把饭局人情、车辆驾驶、项目推进和冲动决策合并观察，避免每项都单独刷屏。
  - 改革要三思对应风险损耗类的冲动决策和规则边界，不应直接写成好坏结论。
- 调权建议：
  - 商务谈判：责任、新机遇、招募合作同段出现时，合作机会应进入项目/合同类候选。

### 3-4 月
- 师傅原文：责任，有人招募合作，有新机遇，要求稳而行，亲人。
- 师傅事件映射：责任增加(responsibility_increase)、商业合作(business_partnership)、合作机会(cooperation_opportunity)、项目突破(project_breakthrough)、贵人协助(nobleman_help)、家庭事务(family_issue)
- 系统 Top3：合作机会(cooperation_opportunity)、项目突破(project_breakthrough)、relationship_family_cluster(relationship_family_cluster)、暗中帮助(hidden_help)
- 命中：合作机会(cooperation_opportunity)、项目突破(project_breakthrough)
- 语义命中：商业合作(business_partnership)、贵人协助(nobleman_help)、家庭事务(family_issue)
- 漏项：责任增加(responsibility_increase)
- 覆盖率：0.833
- 蒸馏观察：
  - 责任和招募合作说明师傅把机会与压力放在同一组里看，不是只说贵人或只说事业好。
  - 稳而行说明新机遇需要落到流程、合同、分工和节奏，不宜只按机会放大。
  - 亲人提示年支、印星或家庭宫位类信息需要进入现实事件解释。
- 调权建议：
  - 责任增加：师傅样本原文“责任，有人招募合作，有新机遇，要求稳而行，亲人。”中出现该现实事件，建议检查其触发规则和排序权重。

### 5-6 月
- 师傅原文：酒友，不要担保，资金会被套住，防破财，忽然有奇迹。
- 师傅事件映射：酒局应酬(social_drinking)、人情往来(favor_obligation)、借贷往来(debt_borrowing)、现金流压力(cashflow_pressure)、投资谨慎(investment_risk)、支出增加(wealth_outflow)、项目财务转机(business_surprise)
- 系统 Top3：expense_vehicle_cluster(expense_vehicle_cluster)、被套住(trapped_commitment)、项目财务转机(business_surprise)、人情往来(favor_obligation)
- 命中：人情往来(favor_obligation)、现金流压力(cashflow_pressure)、支出增加(wealth_outflow)、项目财务转机(business_surprise)
- 语义命中：酒局应酬(social_drinking)、借贷往来(debt_borrowing)、投资谨慎(investment_risk)
- 漏项：无
- 覆盖率：1.000
- 蒸馏观察：
  - 这组体现了师傅把酒友、人情、担保、资金套住放在同一条风险链里看。
  - 防破财不是单独财星判断，更像比劫、人情义务、现金流压力和投资风险共同触发。
  - 忽然有奇迹说明同一组里也可能有转机，但不能把转机解读成无条件收益。
- 调权建议：
  - 当前段落已有基本覆盖，后续只需观察排序是否贴近用户感知。

### 7-8 月
- 师傅原文：台风天，耗气，不要贪，计划以小，小心小人。
- 师傅事件映射：行程延误(travel_delay)、状态波动(health_fluctuation)、过劳疲劳(overwork)、冲动决策(impulsive_decision)、小额损耗(minor_loss)、口舌是非(gossip_dispute)、误会风险(misunderstanding_risk)
- 系统 Top3：状态波动(health_fluctuation)、冲动决策(impulsive_decision)、口舌是非(gossip_dispute)、行程延误(travel_delay)
- 命中：行程延误(travel_delay)、状态波动(health_fluctuation)、冲动决策(impulsive_decision)、口舌是非(gossip_dispute)
- 语义命中：过劳疲劳(overwork)、误会风险(misunderstanding_risk)
- 漏项：小额损耗(minor_loss)
- 覆盖率：0.857
- 蒸馏观察：
  - 台风天可以理解为外部环境扰动，不应只映射成出行，而应兼看计划延误、状态消耗和风险控制。
  - 不要贪与计划以小，说明师傅在这一组降低扩张建议，更强调缩小动作和保守执行。
  - 小人提醒不宜写成恐吓，应落到口舌、误会、同业竞争或暗中阻力。
- 调权建议：
  - 小额损耗：将“改革三思、不要贪、小心小人”转译为小额损耗、误会和口舌风险的降级提醒。

### 9-10 月
- 师傅原文：女友味，综合公司，房、店、车，担重心累。
- 师傅事件映射：关系推进(relationship_progress)、伴侣规划(partner_planning)、商业合作(business_partnership)、门店经营(store_operation)、房产居住(property_housing)、店铺门面(shop_property)、大件资产购买(asset_purchase)、车辆支出(vehicle_expense)、责任增加(responsibility_increase)、情绪压力(emotional_pressure)
- 系统 Top3：情绪压力(emotional_pressure)、relationship_family_cluster(relationship_family_cluster)、客户成交(sales_conversion)、房产居住(property_housing)、expense_vehicle_cluster(expense_vehicle_cluster)、门店经营(store_operation)
- 命中：门店经营(store_operation)、房产居住(property_housing)、车辆支出(vehicle_expense)、情绪压力(emotional_pressure)
- 语义命中：关系推进(relationship_progress)、伴侣规划(partner_planning)、商业合作(business_partnership)、店铺门面(shop_property)、大件资产购买(asset_purchase)
- 漏项：责任增加(responsibility_increase)
- 覆盖率：0.900
- 蒸馏观察：
  - 这一组最有现实物象：关系、公司、房、店、车一起出现，说明师傅会把财星、日支、事业平台和资产物象合看。
  - 房店车不应简单等于买房买车，也可能是看房、店铺门面、车辆支出、资产添置或相关合同。
  - 担重心累提示好事和压力并行，系统输出时要同时给机会、成本和责任说明。
- 调权建议：
  - 责任增加：师傅样本原文“女友味，综合公司，房、店、车，担重心累。”中出现该现实事件，建议检查其触发规则和排序权重。

### 11-12 月
- 师傅原文：有110的警告，压力而压抑，逢财置物。
- 师傅事件映射：投诉争议(official_dispute)、规则处罚(rule_penalty)、规则合规(legal_compliance)、情绪压力(emotional_pressure)、现金流压力(cashflow_pressure)、大件资产购买(asset_purchase)、设备采购(equipment_purchase)、房产居住(property_housing)
- 系统 Top3：大件资产购买(asset_purchase)、expense_vehicle_cluster(expense_vehicle_cluster)、情绪压力(emotional_pressure)、投诉争议(official_dispute)
- 命中：投诉争议(official_dispute)、情绪压力(emotional_pressure)、现金流压力(cashflow_pressure)、大件资产购买(asset_purchase)、设备采购(equipment_purchase)
- 语义命中：规则处罚(rule_penalty)、规则合规(legal_compliance)、房产居住(property_housing)
- 漏项：无
- 覆盖率：1.000
- 蒸馏观察：
  - 110 警告不能写成会出事，应转译成规则、纠纷、处罚、安全边界或报警类提醒。
  - 压力而压抑说明官杀压力、规则约束或现实责任可能更重，健康状态也要以情绪压力表达。
  - 逢财置物把财务事件和大件添置连接起来，系统应区分收入、支出、置物和资产转换。
- 调权建议：
  - 当前段落已有基本覆盖，后续只需观察排序是否贴近用户感知。

## 下一步调权原则
- 不把师傅样本写成硬覆盖规则，只作为排序和组合解释的校准样本。
- 优先让已有候选池中的事件进入合适段落 Top3，而不是盲目扩展事件数量。
- 高风险表达需要转译成用户可读的安全提醒，例如 110 对应规则边界、报警边界或合规提醒。
- 若某个样本事件完全没有事件库支撑，再补事件库；已有事件则优先调触发链和排序权重。
