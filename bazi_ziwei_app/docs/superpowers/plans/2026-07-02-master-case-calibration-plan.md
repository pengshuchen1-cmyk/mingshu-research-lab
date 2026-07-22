# Chen Pengshu Master Case Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the real 2026 monthly-event case for 陈芃澍 as a calibration reference without overriding the main prediction rules.

**Architecture:** Store the case as a JSON rule-style reference under `rules/`, register the source in `source_registry.json`, and document the distilled reasoning under `docs/reports/`. Tests verify the case remains structured, traceable, and safe for future evidence-chain calibration.

**Tech Stack:** Python unittest, JSON rule files, Markdown documentation.

## Global Constraints

- Do not treat the master case as an absolute prediction rule.
- Preserve uncertain transcription in review-only fields.
- Keep all user-visible wording in Chinese.
- Avoid forbidden absolute expressions.
- Keep the current Streamlit UI unchanged.

---

### Task 1: Add Master Case Fixture

**Files:**
- Create: `rules/master_case_references.json`
- Modify: `rules/source_registry.json`
- Test: `tests/test_master_case_references.py`

**Interfaces:**
- Produces: `rules/master_case_references.json` with top-level `rules` list.
- Consumes: `rules/source_registry.json` source id `master_case_chen_pengshu_2026`.

- [x] **Step 1: Write the failing test**

Run: `.venv/bin/python -m unittest tests.test_master_case_references -v`

Expected: fail because `rules/master_case_references.json` does not exist.

- [x] **Step 2: Add JSON reference**

Create one case with six two-month periods and map each period to existing event types.

- [x] **Step 3: Register source**

Add `master_case_chen_pengshu_2026` to source registry as `命例参考`.

- [x] **Step 4: Run tests**

Run: `.venv/bin/python -m unittest tests.test_master_case_references -v`

Expected: pass.

### Task 2: Add Distillation Report

**Files:**
- Create: `docs/reports/master_case_chen_pengshu_2026_distillation.md`
- Test: `tests/test_master_case_references.py`

**Interfaces:**
- Produces: a human-readable report naming event patterns and explaining how the master case can calibrate evidence chains.

- [x] **Step 1: Write report**

Cover alcohol/social scenes, driving, project opportunity, recruitment/cooperation, trapped funds, property/shop/car objects, 110 warning, and purchase-on-wealth signal.

- [x] **Step 2: Run tests**

Run: `.venv/bin/python -m unittest tests.test_master_case_references -v`

Expected: pass.

