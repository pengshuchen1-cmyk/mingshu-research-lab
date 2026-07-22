# 删除 40 组虚构命例链路与审计设计

日期：2026-07-22

## 目标

彻底移除项目中以 40 组虚构命例为对象的生成、完整报告链路、差异性审计、冻结样本、验收产物和测试。此后八字重构只使用用户指定的 5 个真实命例验收。

## 采用方案

采用硬删除，不保留兼容入口、空壳模块、跳过标记或历史审计产物。这样可以避免旧的 40 组链路继续增加测试耗时，也避免开发者误把它当成现行验收标准。

## 删除范围

删除以下 40 组专属资产：

- `core/diversity_audit.py`
- `scripts/build_final_40_case_matrix.py`
- `scripts/run_final_40_case_audit.py`
- `tests/fixtures/final_40_bazi_cases.json`
- `acceptance_samples/final_40_case_audit.json`
- `acceptance_samples/final_40_case_audit.md`
- `tests/test_final_40_case_matrix.py`
- `tests/test_final_40_case_usability.py`
- `tests/test_final_40_case_diversity.py`
- `tests/test_final_40_case_audit_report.py`

其中 `tests/test_final_40_case_matrix.py` 虽已改为检查 5 个命例，但文件名和历史职责仍属于旧闸门，且其断言已由正式的 5 命例测试覆盖，因此一并删除。

## 保留范围

保留并继续作为验收标准：

- `tests/fixtures/user_five_bazi_cases.json`
- `tests/test_user_five_bazi_acceptance.py`
- `tests/test_user_five_ai_acceptance.py`
- `scripts/render_user_five_bazi_acceptance.py`
- `scripts/run_user_five_ai_acceptance.py`
- `acceptance_samples/user_five_bazi_acceptance.md`
- `acceptance_samples/user_five_ai_acceptance.md`

保留正常产品需要的排盘、报告、AI 问答以及不依赖 40 组冻结样本的通用测试。不会因为名称中含有 `audit` 或 `diversity` 就删除紫微算法审查、通用报告差异检查或其他独立能力。

## 验证方式

1. 全项目搜索 `final_40`、`diversity_audit`、`40 组` 等旧标识，确认无运行时或测试依赖残留。
2. 重新生成并核对 5 个真实命例的八字验收产物。
3. 运行 5 命例排盘与 AI 问答验收测试。
4. 运行删除后的全部剩余测试，要求零失败。
5. 检查工作区差异，确认只删除上述旧资产并保留 5 命例链路。

## 完成标准

- 项目中不存在可运行的 40 组虚构命例生成或审计入口。
- 旧冻结样本和旧审计报告均已删除。
- 5 个真实命例仍是唯一明确的八字重构验收集。
- 删除后的全部剩余测试通过。
