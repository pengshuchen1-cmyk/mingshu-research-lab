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


def test_ai_answer_requires_evidence_and_rejects_unknown_fields():
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer.model_validate(_valid_answer())
    assert answer.analysis_conclusion

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate({**_valid_answer(), "extra": "not allowed"})
    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate({**_valid_answer(), "chart_evidence": []})


def test_ai_config_is_disabled_without_key(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = AIConfig.from_environment()

    assert config.enabled is False
    assert config.model == "gpt-5.6-sol"
    assert config.reasoning_effort == "medium"


def test_ai_config_validates_server_overrides(monkeypatch):
    from core.ai_models import AIConfig

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
