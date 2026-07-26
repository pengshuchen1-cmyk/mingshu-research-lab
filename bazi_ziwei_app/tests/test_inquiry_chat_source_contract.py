from __future__ import annotations


def test_answer_source_labels_are_explicit_and_stable():
    from ui.inquiry_page import answer_source_label

    assert answer_source_label("cloud_validated", None) == "Kimi 云端分析 · 本地规则校验"
    assert (
        answer_source_label("local_rules", "missing_api_key")
        == "本地完整分析 · 云端服务未配置"
    )
    assert (
        answer_source_label("local_rules", "insufficient_quota")
        == "本地完整分析 · 云端额度不足"
    )
    assert (
        answer_source_label("local_rules", "network_error")
        == "本地完整分析 · 网络或服务异常"
    )
    assert (
        answer_source_label("local_rules", "local_validation_failed")
        == "本地完整分析 · 云端回答校验未通过"
    )


def test_degradation_warnings_are_reason_specific_and_always_explain_fallback():
    from ui.inquiry_page import degradation_warning

    expected_fragments = {
        "missing_api_key": "未配置 AI 服务",
        "insufficient_quota": "余额或额度不足",
        "invalid_credentials": "API Key 无效或无权限",
        "rate_limited": "网络或 AI 服务出现短暂异常",
        "network_error": "网络或 AI 服务出现短暂异常",
        "timeout": "网络或 AI 服务出现短暂异常",
        "service_unavailable": "网络或 AI 服务出现短暂异常",
        "local_validation_failed": "未通过本地四柱规则校验",
    }
    for reason, fragment in expected_fragments.items():
        warning = degradation_warning(reason)
        assert fragment in warning
        assert "当前已切换为本地四柱规则完整分析" in warning
        assert "回应可能不如云端 AI 分析全面" in warning


def test_only_explicit_quota_warning_mentions_balance_or_credit():
    from ui.inquiry_page import degradation_warning

    reasons = (
        "missing_api_key",
        "insufficient_quota",
        "invalid_credentials",
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
        "unparseable_response",
        "local_validation_failed",
    )

    mentions = {
        reason
        for reason in reasons
        if "余额或额度不足" in degradation_warning(reason)
    }
    assert mentions == {"insufficient_quota"}


def test_suggested_questions_cover_primary_customer_domains():
    from ui.inquiry_page import SUGGESTED_QUESTIONS

    text = "\n".join(SUGGESTED_QUESTIONS)
    for keyword in ("强弱", "财运", "事业", "姻缘", "未来一年"):
        assert keyword in text
