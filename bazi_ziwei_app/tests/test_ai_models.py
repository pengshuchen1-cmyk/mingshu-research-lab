from __future__ import annotations

import pytest
from pydantic import ValidationError


def _valid_answer():
    return {
        "analysis_conclusion": "这是基于命盘事实的趋势分析。",
        "chart_evidence": ["日主乙木"],
        "rule_evidence": ["强弱先看月令与通根"],
        "timing_conditions": ["具体阶段需要结合流年观察"],
        "practical_advice": ["结合现实选择验证"],
        "uncertainty_limitations": ["命理趋势不保证现实结果"],
    }


def test_ai_answer_allows_empty_machine_lists_and_rejects_unknown_fields():
    from core.ai_models import BaziAIAnswer

    data = {
        "analysis_conclusion": "这是可直接展示的自然回答。",
        "chart_evidence": [],
        "rule_evidence": [],
        "timing_conditions": [],
        "practical_advice": [],
        "uncertainty_limitations": [],
    }
    answer = BaziAIAnswer.model_validate(data)
    assert answer.analysis_conclusion

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate({**data, "extra": "not allowed"})


def test_cloud_analysis_contract_accepts_only_claim_linked_segments():
    from core.ai_models import CloudBaziAnalysis

    result = CloudBaziAnalysis.model_validate(
        {
            "segments": [
                {
                    "claim_ids": ["wealth-2027"],
                    "text": "依据本地事实展开的自然回答。",
                }
            ]
        }
    )

    assert result.segments[0].claim_ids == ["wealth-2027"]
    with pytest.raises(ValidationError):
        CloudBaziAnalysis.model_validate(
            {
                "segments": [
                    {
                        "claim_ids": ["wealth-2027"],
                        "text": "回答",
                        "rule_evidence": ["模型改写的规则"],
                    }
                ],
            }
        )


def test_resolved_question_and_cloud_segments_are_strict():
    from core.ai_models import CloudBaziAnalysis, ResolvedQuestion

    resolved = ResolvedQuestion(
        safe_question="明年每个月财运如何",
        domain="wealth",
        subdomains=["timing"],
        time_scope="month_range",
        target_years=[2027],
        target_months=list(range(1, 13)),
        requested_depth="monthly",
        interpretation_receipt="本次按2027丁未年1—12月分析。",
        current_marriage_status_requested=False,
    )
    assert resolved.target_years == [2027]
    assert resolved.target_months[-1] == 12
    assert resolved.model_dump()["current_marriage_status_requested"] is False

    cloud = CloudBaziAnalysis(
        segments=[{"claim_ids": ["wealth-2027"], "text": "先看现金流。"}]
    )
    assert cloud.segments[0].claim_ids == ["wealth-2027"]

    with pytest.raises(ValidationError):
        CloudBaziAnalysis(
            segments=[
                {"claim_ids": ["wealth-2027"], "text": "正常", "secret": "x"}
            ]
        )


def test_ai_config_is_disabled_without_key(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    monkeypatch.delenv("MINGSHU_AI_PROVIDER", raising=False)
    config = AIConfig.from_environment()

    assert config.enabled is False
    assert config.provider == "kimi"
    assert config.model == "kimi-k3"
    assert config.reasoning_effort == "low"


def test_ai_config_validates_server_overrides(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "server-secret")
    monkeypatch.setenv("MINGSHU_AI_MODEL", "gpt-5.6-terra")
    monkeypatch.setenv("MINGSHU_AI_REASONING", "high")
    monkeypatch.setenv("MINGSHU_AI_TIMEOUT_SECONDS", "45")

    config = AIConfig.from_environment()

    assert config.enabled is True
    assert config.api_key == "server-secret"
    assert config.model == "gpt-5.6-terra"
    assert config.reasoning_effort == "high"
    assert config.timeout_seconds == 45


def test_kimi_is_default_and_streamlit_secrets_enable_cloud(monkeypatch):
    from core.ai_models import AIConfig

    for name in (
        "MINGSHU_AI_PROVIDER",
        "MOONSHOT_API_KEY",
        "MINGSHU_AI_MODEL",
        "MINGSHU_AI_BASE_URL",
        "MINGSHU_AI_REASONING",
    ):
        monkeypatch.delenv(name, raising=False)

    config = AIConfig.from_environment(
        {"MOONSHOT_API_KEY": "local-secret"}
    )

    assert config.enabled is True
    assert config.api_key == "local-secret"
    assert config.provider == "kimi"
    assert config.model == "kimi-k3"
    assert config.base_url == "https://api.moonshot.cn/v1"
    assert config.reasoning_effort == "low"


def test_server_environment_overrides_streamlit_secrets(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_PROVIDER", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "server-secret")
    monkeypatch.setenv("MINGSHU_AI_MODEL", "kimi-k3")
    monkeypatch.setenv("MINGSHU_AI_BASE_URL", "https://api.moonshot.cn/v1")
    monkeypatch.setenv("MINGSHU_AI_REASONING", "max")

    config = AIConfig.from_environment(
        {
            "MOONSHOT_API_KEY": "local-secret",
            "MINGSHU_AI_MODEL": "should-not-win",
        }
    )

    assert config.api_key == "server-secret"
    assert config.model == "kimi-k3"
    assert config.reasoning_effort == "max"


def test_ai_config_allows_single_90_second_request(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_TIMEOUT_SECONDS", "120")

    config = AIConfig.from_environment()

    assert config.timeout_seconds == 90


def test_openai_provider_keeps_its_own_key(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

    config = AIConfig.from_environment()
    assert config.provider == "openai"
    assert config.api_key == "openai-secret"
