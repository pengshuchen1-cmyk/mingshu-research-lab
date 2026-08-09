# Bazi Ziwei App Agent Guide

## Repository profile

- This directory is a Python 3.11 Streamlit application. `app.py` is the entry point, and the local development port is 8501.
- Runtime dependencies are pinned in `requirements.txt`. There is no `pyproject.toml`, lockfile, dev-requirements file, lint configuration, type-check configuration, or configured CI pipeline.
- Use the existing `.venv` for repository commands. `pytest` is installed in the current environment but is not declared in `requirements.txt`; do not silently change dependencies to hide that reproducibility gap.
- The default runtime mode is public. Set exactly `MINGSHU_RUNTIME_MODE=local` only for trusted local use where SQLite profile persistence is intended.
- The Git root is the parent research-lab repository. Always inspect `git status` from this directory and preserve unrelated work in sibling projects and this app.

## Important paths and architecture

- `app.py`: Streamlit bootstrap, routing, session orchestration, and public-release checks.
- `ui/`: pages, components, styles, profile confirmation, and session-state flows. Register pages through the existing `app.py::get_pages` path.
- `core/`: deterministic chart/rule engines and AI orchestration.
- Canonical four-pillars flow: `core/bazi_calendar_adapter.py` -> `core/four_pillars_engine.py` -> `core/bazi_engine.py` -> canonical `ChartFacts` in `core/chart_facts.py`.
- `services/`: AI provider adapters. Supported providers are Kimi Chat Completions and OpenAI Responses.
- `rules/`: local rule data. `rules/bazi_skill/` is integrity-protected by a SHA-256 manifest.
- `report/`: Markdown, text, and PDF report generation.
- `utils/`: runtime mode, SQLite, backup, logging, privacy/session, and release-safety utilities.
- `tests/`: pytest collection of both pytest-style tests and `unittest.TestCase` suites. Autouse fixtures default tests to local mode and reset AI request-controller state.

## Core invariants

### Deterministic domain authority

- The local explicit rule engine is the sole authority for four pillars, qiyun, strength, patterns, and other chart conclusions. Use `lunar_python` only for calendar conversion, exact jieqi, and the day seed already delegated to it.
- Do not calculate parallel chart facts in UI, report, or AI layers. Pass the canonical `ChartFacts` model downstream.
- Preserve the input flow: profile form -> chart preview -> input fingerprint verification -> confirmed chart. Do not construct a chart from unconfirmed inputs.
- `BirthInput` supports `china_standard` only. Do not reintroduce legacy longitude or true-solar-time behavior without an explicit product decision and migration plan.
- Treat lichun, exact jieqi, the 23:00 day boundary, leap months, unknown birth hour, and qiyun as high-risk regression areas.

### Privacy and runtime isolation

- Public mode is session-only. It must not read or write the local profile SQLite database, backups, or persistent application logs. Public sessions contain sensitive birth data and must retain the existing TTL and chart-switch cleanup behavior.
- Local mode may use `data/profiles.db`; schema migrations, imports, restores, and backups are destructive/high-risk paths. Require backups, transactions, idempotency, and focused tests.
- Log only existing allowlisted, sanitized metadata. Never log or persist raw prompts, model answers, chart payloads, names, birth data, locations, profile IDs, API keys, secrets, or high-entropy credentials.
- Public export names must not contain PII, and public exports must not create server-side customer files.
- Escape every dynamic value with `html.escape` before interpolating it into `unsafe_allow_html=True` markup.
- Never inspect, print, or commit `.env`, `.streamlit/secrets.toml`, real API keys, customer exports, or `data/profiles.db`. Use `.env.example` only for documented variable names.

### AI boundary

- Build provider requests from canonical local facts through the existing FactPacket and AnalysisPlan pipeline. Construct a safe local answer before any cloud call.
- Preserve scope gating, prompt-injection rejection, PII/secret redaction, strict Pydantic schemas (`extra="forbid"`), output segment guards, conflict replacement, and all-unsafe local fallback.
- The orchestrator may invoke provider generation at most once. Kimi uses its existing fixed model, strict JSON response schema, and explicitly disabled SDK retries. OpenAI uses the Responses API with `store=False` and no Conversations state, but its client currently inherits the OpenAI SDK retry default. Treat that as a known cost/rate-limit gap; do not claim OpenAI is no-retry until the client and regression tests enforce it.
- Never send raw PII, complete profiles, locations, identifiers, internal versions, logs, configuration, or secrets to providers. Never expose an API key in the browser or UI.
- Process-local request controls, caches, and rate limits are not multi-instance guarantees; do not describe them as distributed protection.

## Common commands

```bash
# First-time runtime setup: create .venv with a Python 3.11 interpreter through
# the host's version manager. Once it exists, verify and activate it.
.venv/bin/python --version
source .venv/bin/activate
python -m pip install -r requirements.txt

# Environment and dependency checks.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python check_env.py
.venv/bin/python -m pip check

# Local application. The helper script is also supported on macOS: bash run_mac.sh
MINGSHU_RUNTIME_MODE=local .venv/bin/python -m streamlit run app.py --server.port 8501

# Focused, single-case, and full regression tests.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_<area>.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_<area>.py::test_name -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

# Syntax/import compilation without writing caches into the repository.
PYTHONPYCACHEPREFIX=/tmp/mingshu-pycache .venv/bin/python -m compileall -q \
  app.py core report services ui utils tools scripts

# Special validation gates. Docker/Compose must be installed for the second command.
.venv/bin/python tools/validate_event_chain_quality.py
docker compose config --quiet
```

Only after an intentional change to `rules/bazi_skill/*.json`, run:

```bash
.venv/bin/python tools/rebuild_bazi_rule_manifest.py
```

This command updates integrity metadata; review and test that generated diff. There is no configured lint, formatter, type-check, or coverage command, so do not claim one ran. Do not use `unittest discover` as the full-suite gate because pytest is the repository-wide collector.

## Change workflow

1. Read the request, this file, the relevant execution path, and nearby tests. Check `git status` before editing and preserve all unrelated user changes.
2. Make the smallest cohesive change. Follow existing Python and Streamlit patterns; avoid parallel implementations of domain facts, storage, provider clients, or navigation.
3. Add focused deterministic regression coverage. Use fakes for AI/network boundaries, `tmp_path` for files and SQLite, and synthetic non-customer fixtures.
4. Run the focused test first. For application-code changes, finish with full pytest, `check_env.py`, `pip check`, and compileall. Add the risk-specific gates below.
5. For `rules/bazi_skill/*.json`, rebuild and verify the manifest. For monthly event logic, run `tools/validate_event_chain_quality.py`; exit 0 does not by itself prove content quality.
6. For UI changes, run relevant page/component tests and a Streamlit health smoke; perform an interactive browser check when layout or interaction is material.
7. For database/privacy changes, test both public and local modes using temporary storage. Never touch the real profile database.
8. For deployment changes, run `tests/test_deployment_assets.py` and `docker compose config --quiet`. Do not build, start, deploy, or publish containers unless explicitly requested.
9. Summarize changed files, exact checks, known baseline failures, and residual risk. Do not commit or push unless the user explicitly requests it.

Known baseline on 2026-08-09: a `HEAD` source snapshot passed 1638 tests and failed 4; one failure was caused by the snapshot lacking `.git` metadata, while 3 deployment-asset failures in `tests/test_deployment_assets.py` are reproducible in the real checkout. Those failures cover container non-root/public/health configuration, Chinese PDF fonts, and Compose public environment variables. Re-run and report the current baseline rather than assuming these remain unchanged. Git-aware tests require a real checkout and may fail spuriously in a source archive.

## Multi-agent workflow

Use the project agents in `.codex/agents/` for non-trivial work that benefits from separable implementation, review, and verification. The primary agent owns scope, sequencing, evidence reconciliation, and the final answer.

1. Delegate implementation to `developer` with explicit behavior, constraints, files in scope, and acceptance criteria.
2. Wait for `developer` before starting another writer. Then run `reviewer` and `test_engineer` in parallel. `reviewer` is always read-only; `test_engineer` may edit tests only when the delegation explicitly grants test ownership.
3. Give each writer clear file ownership, remind it that others share the worktree, and prohibit reverting unrelated edits.
4. Send reproducible review findings or test failures back to `developer` for the smallest fix. Re-review changed risk areas and rerun affected gates.
5. Wait for every delegated agent, resolve conflicting conclusions against repository evidence, and deliver one consolidated result.

Handle trivial, tightly coupled, documentation-only, or agent-configuration-only work directly when delegation would add no useful independent verification.

## Test conventions

- Use pytest as the standard runner. Keep tests under `tests/test_*.py`; match the nearest suite's pytest or `unittest.TestCase` style.
- Use descriptive behavior names, deterministic inputs, and Arrange-Act-Assert. Cover success, validation/error, boundary, privacy/isolation, fallback, cache/session invalidation, and concurrency where relevant.
- Stub providers and external boundaries. Never make real network calls, use live flags, read secrets, or rely on production endpoints.
- Restore monkeypatches, environment variables, module state, request-controller registries, and Streamlit session state after each test.
- For UI behavior, prefer Streamlit `AppTest`, component mocks, and user-visible assertions. Use source-contract tests only for structural/privacy/release invariants that cannot be exercised more directly.
- A passing collection, compileall, coverage report, or health endpoint is supporting evidence, not proof of behavior or visual correctness.

## Code review rules

- Lead with findings ordered by severity. Include exact file/line references, the execution or reproduction path, impact, and a concrete remediation direction.
- Prioritize privacy/public-local isolation, secret and PII flow, release safety, AI request/output guards, HTML escaping, canonical chart facts, calendar boundaries, rule integrity, database safety, session leakage, and missing behavioral tests.
- Treat deployment assets as security-sensitive: reconcile Dockerfile, Compose, Caddy, environment propagation, health checks, secret exclusions, and non-root execution as one executable architecture.
- Do not report formatting or subjective refactors unless they cause a concrete correctness or maintenance risk.
- If no defect is found, state that explicitly and disclose untested browser, container, network, or multi-instance paths.
