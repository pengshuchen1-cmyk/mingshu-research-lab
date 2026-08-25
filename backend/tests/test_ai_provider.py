import json
from types import SimpleNamespace

from app.ai.ai_models import (
    AIConfig,
    AIRequestContext,
    AnalysisPlan,
    ClaimPlan,
    FactItem,
    FactPacket,
    ResolvedQuestion,
)
from app.ai.providers.ai_service_errors import classify_service_error
from app.ai.providers.kimi_bazi_client import KimiBaziClient


class _FakeCompletions:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] = {}

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content=json.dumps(
                            {
                                "segments": [
                                    {
                                        "claim_ids": ["claim.overview"],
                                        "text": "结构化云回答",
                                    }
                                ]
                            },
                            ensure_ascii=False,
                        )
                    ),
                )
            ],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=8),
        )


class _FakeClient:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def _context() -> AIRequestContext:
    resolved = ResolvedQuestion(
        safe_question="命盘整体特点是什么？",
        domain="overview",
    )
    fact = FactItem(
        id="chart.day_master",
        kind="day_master",
        text="日主为甲木",
        source="chart",
    )
    packet = FactPacket(
        resolved=resolved,
        facts=[fact],
        rule_evidence=[{"id": "rule.overview", "text": "依据日主分析"}],
    )
    plan = AnalysisPlan(
        resolved=resolved,
        claims=[
            ClaimPlan(
                id="claim.overview",
                topic="整体特点",
                allowed_conclusion="结合甲木说明整体特点",
                local_text="本地规则回答",
                fact_ids=[fact.id],
                rule_ids=["rule.overview"],
            )
        ],
    )
    return AIRequestContext(
        question=resolved.safe_question,
        category="overview",
        requires_timing=False,
        chart_facts={"day_master": "甲"},
        rule_evidence=packet.rule_evidence,
        resolved_question=resolved,
        fact_packet=packet,
        analysis_plan=plan,
    )


def test_kimi_client_uses_configured_model_without_hardcoded_allowlist():
    fake = _FakeClient()
    config = AIConfig(
        api_key="test-key",
        enabled=True,
        model="kimi-k2.6",
        provider="kimi",
        base_url="https://api.moonshot.cn/v1",
    )

    generation = KimiBaziClient(config, client=fake).answer(_context())

    assert fake.completions.kwargs["model"] == "kimi-k2.6"
    assert fake.completions.kwargs["extra_body"] == {
        "thinking": {"type": "disabled"}
    }
    assert generation.analysis.segments[0].text == "结构化云回答"
    assert generation.input_tokens == 12
    assert generation.output_tokens == 8


def test_kimi_environment_default_tracks_available_general_model(monkeypatch):
    monkeypatch.delenv("MINGSHU_AI_MODEL", raising=False)
    config = AIConfig.from_environment(
        {
            "MINGSHU_AI_PROVIDER": "kimi",
            "MOONSHOT_API_KEY": "test-key",
        }
    )

    assert config.enabled is True
    assert config.model == "kimi-k2.6"
    assert config.kimi_thinking is False
    assert config.timeout_seconds == 90


def test_kimi_thinking_can_be_enabled_explicitly():
    fake = _FakeClient()
    config = AIConfig(
        api_key="test-key",
        enabled=True,
        model="kimi-k2.6",
        provider="kimi",
        base_url="https://api.moonshot.cn/v1",
        reasoning_effort="low",
        kimi_thinking=True,
    )

    KimiBaziClient(config, client=fake).answer(_context())

    assert fake.completions.kwargs["extra_body"] == {
        "reasoning_effort": "low"
    }


def test_missing_provider_model_is_classified_separately():
    error = RuntimeError("requested model was not found")
    error.status_code = 404  # type: ignore[attr-defined]
    error.code = "model_not_found"  # type: ignore[attr-defined]

    assert classify_service_error(error) == "model_unavailable"
