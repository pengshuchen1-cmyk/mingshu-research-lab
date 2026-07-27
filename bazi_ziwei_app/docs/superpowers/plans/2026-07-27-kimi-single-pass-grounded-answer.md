# Kimi Single-Pass Grounded Answer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each customer question perform at most one Kimi request, accept natural paraphrasing without weakening factual guards, and attach all machine evidence from the local Four Pillars rules.

**Architecture:** Kimi returns a minimal structured `CloudBaziAnalysis` containing only the customer-facing natural answer. The orchestrator validates only that cloud prose, then replaces all machine evidence fields with the deterministic fields from `build_local_answer(context)`. Provider retries and application-level corrective retries are removed; the configured request boundary is 90 seconds.

**Tech Stack:** Python 3, Pydantic 2, OpenAI-compatible Kimi Chat Completions, Streamlit, pytest.

## Global Constraints

- Local “四柱八字分析规则” remains the only source of chart facts and machine evidence.
- Kimi remains `kimi-k3` with `reasoning_effort=low`.
- Each customer question may call the cloud provider at most once.
- Explicit chart contradictions and deterministic promises must still be rejected.
- No real birth case may be embedded in production prompts or rules.
- No identity fields or API Key may appear in requests, responses, or logs.
- Unvalidated streaming fragments must not be shown to customers.

---

### Task 1: Define the cloud-prose contract and Kimi single-request boundary

**Files:**
- Modify: `core/ai_models.py`
- Modify: `services/bazi_ai_prompt.py`
- Modify: `services/kimi_bazi_client.py`
- Test: `tests/test_ai_models.py`
- Test: `tests/test_kimi_bazi_client.py`
- Test: `tests/test_openai_bazi_client.py`

**Interfaces:**
- Produces: `CloudBaziAnalysis(BaseModel)` with `analysis_conclusion: str`.
- Preserves: `KimiBaziClient.answer(context: AIRequestContext) -> BaziAIAnswer`.
- Produces: Kimi JSON Schema named `bazi_cloud_analysis`, based only on `CloudBaziAnalysis`.

- [ ] **Step 1: Write failing cloud-contract and retry tests**

```python
def test_cloud_analysis_contract_accepts_only_natural_answer():
    from core.ai_models import CloudBaziAnalysis

    result = CloudBaziAnalysis.model_validate(
        {"analysis_conclusion": "依据本地事实展开的自然回答。"}
    )
    assert result.analysis_conclusion
    with pytest.raises(ValidationError):
        CloudBaziAnalysis.model_validate(
            {
                "analysis_conclusion": "回答",
                "rule_evidence": ["模型改写的规则"],
            }
        )


def test_kimi_client_requests_only_cloud_prose_and_disables_sdk_retries():
    # Assert OpenAI(..., max_retries=0).
    # Assert response_format schema equals CloudBaziAnalysis.model_json_schema().
    # Assert returned BaziAIAnswer has the cloud conclusion and empty evidence lists.
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_kimi_bazi_client.py \
  tests/test_openai_bazi_client.py -q --tb=short
```

Expected: FAIL because `CloudBaziAnalysis` does not exist, Kimi still uses `BaziAIAnswer` as its response schema, and SDK retries equal one.

- [ ] **Step 3: Implement the minimal cloud-prose contract**

Add to `core/ai_models.py`:

```python
class CloudBaziAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    analysis_conclusion: str = Field(min_length=1, max_length=6000)
```

Change Kimi response parsing to:

```python
parsed = CloudBaziAnalysis.model_validate(json.loads(content))
return BaziAIAnswer(
    analysis_conclusion=parsed.analysis_conclusion,
    chart_evidence=[],
    rule_evidence=[],
    timing_conditions=[],
    practical_advice=[],
    uncertainty_limitations=[],
)
```

Construct the SDK with `max_retries=0`, and build its strict JSON Schema from `CloudBaziAnalysis`.

Update the system prompt to state that only `analysis_conclusion` is returned and that any mentioned strong/weak classification must use the exact supplied local classification without adding a second classification.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the same focused command. Expected: all selected tests pass.

---

### Task 2: Make orchestration single-pass and attach deterministic local evidence

**Files:**
- Modify: `core/ai_orchestrator.py`
- Test: `tests/test_ai_orchestrator.py`
- Test: `tests/test_ai_answer_guard.py`
- Test: `tests/test_user_five_ai_acceptance.py`
- Test: `tests/test_lunar_1999_acceptance.py`

**Interfaces:**
- Produces: `_cloud_prose_candidate(answer: BaziAIAnswer) -> BaziAIAnswer`.
- Produces: `_with_local_evidence(answer: BaziAIAnswer, context: AIRequestContext) -> BaziAIAnswer`.
- Preserves: `answer_question(...) -> AnswerResult`.

- [ ] **Step 1: Replace retry expectations with failing single-pass tests**

```python
def test_orchestrator_does_not_retry_after_guard_rejection():
    fake = _FakeClient([_answer("乙巳日主肯定发财。", "模型证据")])
    result = answer_question(_chart(), "财运如何？", [], config=AIConfig("key", True), client=fake)
    assert result.degraded_reason == "local_validation_failed"
    assert len(fake.contexts) == 1


def test_orchestrator_does_not_retry_malformed_output():
    fake = _FakeClient([AIServiceError("unparseable_response")])
    result = answer_question(_chart(), "财运如何？", [], config=AIConfig("key", True), client=fake)
    assert result.degraded_reason == "unparseable_response"
    assert len(fake.contexts) == 1


def test_cloud_rule_paraphrase_is_replaced_by_local_evidence():
    cloud = _answer(
        "壬日主身弱，财务重点是承载能力和现金流。",
        "云端自行改写、不能逐字映射的证据",
    )
    result = answer_question(_chart(), "财运如何？", [], config=AIConfig("key", True), client=_FakeClient([cloud]))
    assert result.source == "cloud_validated"
    assert "云端自行改写" not in result.rule_evidence
    assert result.rule_evidence
```

Keep a separate test proving that a cloud conclusion saying `壬日主身强` for the canonical `身弱` chart is still rejected.

- [ ] **Step 2: Run the orchestrator tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_orchestrator.py \
  tests/test_ai_answer_guard.py \
  tests/test_user_five_ai_acceptance.py \
  tests/test_lunar_1999_acceptance.py -q --tb=short
```

Expected: retry-count tests and local-evidence replacement test fail against the old two-attempt orchestration.

- [ ] **Step 3: Implement a single provider call**

Replace the two-attempt loop with one call:

```python
try:
    cloud_answer = service.answer(context)
except AIServiceError as exc:
    return _local_result(context, _degradation_reason(exc.code))
except Exception:
    return _local_result(context, "service_unavailable")
```

Validate a cloud-only candidate:

```python
candidate = BaziAIAnswer(
    analysis_conclusion=cloud_answer.analysis_conclusion,
    chart_evidence=[],
    rule_evidence=[],
    timing_conditions=[],
    practical_advice=[],
    uncertainty_limitations=[],
)
guard = validate_ai_answer(candidate, context)
```

After acceptance, attach deterministic local details:

```python
local = build_local_answer(context)
grounded = local.model_copy(
    update={"analysis_conclusion": candidate.analysis_conclusion}
)
return _answer_result(
    grounded,
    source="cloud_validated",
    provider=config.provider,
)
```

If the guard rejects the candidate, immediately return `_local_result(context, "local_validation_failed")`.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the same Task 2 command. Expected: all selected tests pass and every rejected cloud response records exactly one fake-client context.

---

### Task 3: Apply the 90-second deployment boundary and verify the complete product

**Files:**
- Modify: `core/ai_models.py`
- Modify: `.streamlit/secrets.toml.example`
- Modify: `.streamlit/secrets.toml` (ignored local configuration; never commit the Key)
- Modify: `README.md`
- Test: `tests/test_ai_models.py`
- Test: `tests/test_ai_release_privacy.py`

**Interfaces:**
- Preserves: `AIConfig.from_environment(...) -> AIConfig`.
- Changes: accepted timeout range from `5..60` to `5..90`.

- [ ] **Step 1: Write a failing timeout-cap test**

```python
def test_ai_config_allows_single_90_second_request(monkeypatch):
    monkeypatch.setenv("MINGSHU_AI_TIMEOUT_SECONDS", "120")
    config = AIConfig.from_environment()
    assert config.timeout_seconds == 90
```

- [ ] **Step 2: Run the timeout test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_models.py -q --tb=short
```

Expected: FAIL because the current cap is 60 seconds.

- [ ] **Step 3: Implement and document the boundary**

Change the cap to:

```python
timeout_seconds=min(90, max(5, timeout))
```

Set `MINGSHU_AI_TIMEOUT_SECONDS = "90"` in local and example Streamlit secrets. Document `90` in `README.md`, together with single cloud call, local evidence assembly, and no automatic provider retry.

- [ ] **Step 4: Run focused and full verification**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_kimi_bazi_client.py \
  tests/test_ai_orchestrator.py \
  tests/test_ai_answer_guard.py \
  tests/test_ai_release_privacy.py \
  tests/test_user_five_ai_acceptance.py \
  tests/test_lunar_1999_acceptance.py -q --tb=short
```

Then run:

```bash
.venv/bin/python -m pytest -q --tb=short
```

Expected: all tests pass.

- [ ] **Step 5: Restart and perform one live Kimi acceptance request**

Restart Streamlit on `http://127.0.0.1:8501`. Use the 1999 acceptance chart and the wealth/career topic question. Record only elapsed time, answer source, degradation reason and evidence counts; do not print the Key or cloud answer body.

Acceptance:

- exactly one cloud request;
- total time does not exceed the 90-second application boundary;
- `source == "cloud_validated"`;
- local chart and rule evidence are non-empty;
- no local degradation warning is shown.

- [ ] **Step 6: Commit implementation**

Stage only source, tests, documentation and example configuration. Never stage `.streamlit/secrets.toml`.

```bash
git add \
  core/ai_models.py \
  core/ai_orchestrator.py \
  services/bazi_ai_prompt.py \
  services/kimi_bazi_client.py \
  tests/test_ai_models.py \
  tests/test_kimi_bazi_client.py \
  tests/test_openai_bazi_client.py \
  tests/test_ai_orchestrator.py \
  tests/test_ai_answer_guard.py \
  tests/test_user_five_ai_acceptance.py \
  tests/test_lunar_1999_acceptance.py \
  .streamlit/secrets.toml.example \
  README.md \
  docs/superpowers/plans/2026-07-27-kimi-single-pass-grounded-answer.md
git commit -m "fix: make Kimi bazi answers single pass"
```
