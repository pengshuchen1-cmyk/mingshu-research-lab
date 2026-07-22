# Remove Synthetic Forty-Case Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 彻底删除 40 组虚构八字命例的生成、完整报告链路、审计、冻结样本、产物和测试，只保留 5 个真实命例作为本次八字重构验收集。

**Architecture:** 这是一次边界明确的硬删除，不增加兼容层或替代入口。先删除所有 `final_40` 专属资产，再证明 5 命例链路未受影响，最后运行删除后的完整剩余测试集。

**Tech Stack:** Python 3.9、pytest、Git、现有本地八字规则引擎。

## Global Constraints

- 不保留 40 组虚构命例生成器、冻结 JSON、报告链路、差异审计或历史产物。
- 不删除 5 个真实命例的 fixture、排盘验收、AI 验收、生成脚本或验收报告。
- 不删除与 40 组冻结样本无关的通用报告、紫微审查或差异性测试。
- `lunar_python` 仍只用于历法转换、精确节气和日柱种子；本任务不修改排盘算法。
- 所有文件删除使用补丁方式完成，避免宽泛路径或递归删除。

---

### Task 1: 删除 40 组专属实现与资产

**Files:**
- Delete: `core/diversity_audit.py`
- Delete: `scripts/build_final_40_case_matrix.py`
- Delete: `scripts/run_final_40_case_audit.py`
- Delete: `tests/fixtures/final_40_bazi_cases.json`
- Delete: `acceptance_samples/final_40_case_audit.json`
- Delete: `acceptance_samples/final_40_case_audit.md`
- Delete: `tests/test_final_40_case_matrix.py`
- Delete: `tests/test_final_40_case_usability.py`
- Delete: `tests/test_final_40_case_diversity.py`
- Delete: `tests/test_final_40_case_audit_report.py`

**Interfaces:**
- Consumes: 当前分支中已经冻结的 40 组专属模块、脚本、样本和测试。
- Produces: 不再提供 `core.diversity_audit`、`scripts.build_final_40_case_matrix` 或 `scripts.run_final_40_case_audit` 导入入口。

- [ ] **Step 1: 记录删除前的专属依赖**

Run:

```bash
rg --files core scripts tests acceptance_samples | rg "final_40|diversity_audit"
rg -n "diversity_audit|final_40|40 组|40组" core scripts tests acceptance_samples
```

Expected: 文件名搜索列出本任务的 10 个专属文件；内容搜索只显示这些文件之间的导入和说明。若出现其他运行时消费者，先将其加入删除范围并对照设计说明复核。

- [ ] **Step 2: 使用补丁逐一删除 10 个专属文件**

用 `apply_patch` 对上述每个路径执行 `Delete File`。不要使用递归删除，不要匹配通配符，不要删除名称相近的通用审查文件。

- [ ] **Step 3: 验证旧入口和资产已经消失**

Run:

```bash
rg --files core scripts tests acceptance_samples | rg "final_40|diversity_audit"
rg -n "diversity_audit|final_40|40 组|40组" core scripts tests acceptance_samples
```

Expected: 两项搜索都为 exit code 1 且没有输出。

Run:

```bash
git diff --check
```

Expected: exit code 0 且没有输出。

---

### Task 2: 证明 5 个真实命例是唯一验收链路

**Files:**
- Preserve: `tests/fixtures/user_five_bazi_cases.json`
- Preserve: `tests/test_user_five_bazi_acceptance.py`
- Preserve: `tests/test_user_five_ai_acceptance.py`
- Preserve: `scripts/render_user_five_bazi_acceptance.py`
- Preserve: `scripts/run_user_five_ai_acceptance.py`
- Preserve: `acceptance_samples/user_five_bazi_acceptance.md`
- Preserve: `acceptance_samples/user_five_ai_acceptance.md`

**Interfaces:**
- Consumes: `tests/fixtures/user_five_bazi_cases.json` 中 U01–U05 的出生资料与期望四柱。
- Produces: 与当前本地规则引擎一致的排盘验收报告和 AI 问答验收报告。

- [ ] **Step 1: 重新生成 5 命例排盘验收报告**

Run:

```bash
.venv/bin/python scripts/render_user_five_bazi_acceptance.py
```

Expected: exit code 0，更新或确认 `acceptance_samples/user_five_bazi_acceptance.md`，包含 U01–U05 共 5 个命例。

- [ ] **Step 2: 重新生成 5 命例 AI 验收报告**

Run:

```bash
.venv/bin/python -m scripts.run_user_five_ai_acceptance
```

Expected: exit code 0，更新或确认 `acceptance_samples/user_five_ai_acceptance.md`，不访问云端且所有本地问答检查通过。

- [ ] **Step 3: 运行 5 命例专项测试**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_user_five_bazi_acceptance.py tests/test_user_five_ai_acceptance.py
```

Expected: 所有测试通过，exit code 0。

- [ ] **Step 4: 确认验收产物没有意外差异**

Run:

```bash
git diff --exit-code acceptance_samples/user_five_bazi_acceptance.md acceptance_samples/user_five_ai_acceptance.md
```

Expected: exit code 0；若有差异，必须先解释为当前规则引擎的确定性更新并人工核对 U01–U05 四柱，不能直接接受。

---

### Task 3: 运行剩余全量回归并提交删除

**Files:**
- Verify: 全部未删除的 `tests/`
- Commit: Task 1 的 10 个删除文件和本实施计划

**Interfaces:**
- Consumes: 删除 40 组专属测试后的 pytest 收集集。
- Produces: 零失败的剩余项目回归结果，以及一个可审查的删除提交。

- [ ] **Step 1: 运行删除后的全部剩余测试**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: 测试完成、零失败、exit code 0；测试总数应少于删除前的 828 项，因为 40 组专属测试已被移除。

- [ ] **Step 2: 复核最终差异和工作区状态**

Run:

```bash
git diff --check
git status --short
```

Expected: `git diff --check` 为 exit code 0；状态只包含计划内删除和本实施计划，不包含 5 命例产物变化或其他意外修改。

- [ ] **Step 3: 提交硬删除结果**

Run:

```bash
git add core/diversity_audit.py scripts/build_final_40_case_matrix.py scripts/run_final_40_case_audit.py tests/fixtures/final_40_bazi_cases.json acceptance_samples/final_40_case_audit.json acceptance_samples/final_40_case_audit.md tests/test_final_40_case_matrix.py tests/test_final_40_case_usability.py tests/test_final_40_case_diversity.py tests/test_final_40_case_audit_report.py docs/superpowers/plans/2026-07-22-remove-final-40-case-audit.md
git commit -m "test: remove synthetic forty-case audit"
```

Expected: 提交成功；提交内容只有上述删除与实施计划。

- [ ] **Step 4: 提交后再次确认状态**

Run:

```bash
git status --short
git log --oneline -3
```

Expected: 工作区干净，最新提交为 `test: remove synthetic forty-case audit`。
