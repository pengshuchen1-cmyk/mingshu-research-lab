# 事件证据链质量校验报告

基础校验结论：通过

总事件数：162

证据链事件数：98

完整通过数量：98

## 缺字段事件列表

无

## 空字段事件列表

无

## trigger_rules 过弱事件列表

无

## source_ids 缺失事件列表

无

## anti_triggers 需要补强事件列表

无

## variants 需要补强事件列表

无

## 相似度过高事件列表

- `client_payment` 与 `sales_conversion` 的 `trigger_rules` 相似度 0.978
- `client_payment` 与 `side_income` 的 `trigger_rules` 相似度 0.978
- `client_payment` 与 `commission_income` 的 `trigger_rules` 相似度 0.981
- `client_payment` 与 `refund_rebate` 的 `trigger_rules` 相似度 0.978
- `client_payment` 与 `business_cash_in` 的 `trigger_rules` 相似度 0.981
- `client_payment` 与 `wealth_inflow` 的 `trigger_rules` 相似度 1.0
- `project_income` 与 `salary_bonus` 的 `trigger_rules` 相似度 0.978
- `project_income` 与 `resource_monetization` 的 `trigger_rules` 相似度 0.974
- `project_income` 与 `delayed_payment_arrival` 的 `trigger_rules` 相似度 0.981
- `project_income` 与 `asset_appreciation_signal` 的 `trigger_rules` 相似度 0.974
- `project_income` 与 `unexpected_income` 的 `trigger_rules` 相似度 0.981
- `project_income` 与 `business_surprise` 的 `trigger_rules` 相似度 1.0
- 另有 108 项相似度提示，属于后续细化事件触发差异时的优先优化对象。

## 不允许进入 Top 事件的事件列表

无

## 建议优先修复的事件列表

- `client_payment`
- `sales_conversion`
- `side_income`
- `commission_income`
- `refund_rebate`
- `business_cash_in`
- `wealth_inflow`
- `project_income`
- `salary_bonus`
- `resource_monetization`
- `delayed_payment_arrival`
- `asset_appreciation_signal`

## 诊断结论

当前 98 个证据链事件已经具备基础字段、来源依据、触发规则和用户可读解释，可以继续作为高置信度 Top 事件候选。

下一步如果继续扩展事件池，应优先降低同类财务收入事件之间的 `trigger_rules` 相似度，把“客户回款、销售成交、副业收入、佣金提成、退款返利、经营现金流”等事件拆出更明确的结构证据和现实场景差异。
