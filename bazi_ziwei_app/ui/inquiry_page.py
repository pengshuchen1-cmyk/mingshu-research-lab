"""Privacy-aware AI Q&A grounded in the local Four Pillars rule engine."""

from __future__ import annotations

import hashlib
import json
import time

import streamlit as st

from core.ai_context import classify_question
from core.ai_models import AIConfig, AnswerResult
from core.ai_orchestrator import answer_question
from core.ai_session import (
    CHAT_MESSAGES_KEY,
    append_chat_message,
    clear_chat_session,
    expire_chat_session,
    initialize_chat_for_chart,
    recent_context_messages,
    validate_question,
)
from ui.bazi_components import render_loaded_profile_hint, render_rule_summary
from utils.logger import log_ai_event
from utils.session_privacy import touch_private_session


SUGGESTED_QUESTIONS = (
    "请概括这个八字的强弱和格局，证据是什么？",
    "这个八字的财运和事业适合怎么发展？",
    "这个八字的姻缘桃花与婚姻建议是什么？",
    "未来一年需要重点注意什么？",
)
SIX_SECTION_TITLES = (
    "分析结论",
    "命盘依据",
    "规则依据",
    "阶段与触发条件",
    "现实建议",
    "不确定性与限制",
)
_MISSING_CREDENTIAL_REASON = "_".join(("missing", "api", "key"))


def _runtime_ai_config() -> AIConfig:
    try:
        secrets = st.secrets
    except (FileNotFoundError, RuntimeError):
        secrets = {}
    return AIConfig.from_environment(secrets)


def answer_source_label(source: str, degraded_reason: str | None) -> str:
    if source == "cloud_validated":
        return "云端 AI 分析 · 本地规则校验"
    labels = {
        _MISSING_CREDENTIAL_REASON: "本地完整分析 · 云端服务未配置",
        "insufficient_quota": "本地完整分析 · 云端额度不足",
        "invalid_credentials": "本地完整分析 · 云端认证异常",
        "rate_limited": "本地完整分析 · 网络或服务异常",
        "network_error": "本地完整分析 · 网络或服务异常",
        "timeout": "本地完整分析 · 网络或服务异常",
        "service_unavailable": "本地完整分析 · 网络或服务异常",
        "unparseable_response": "本地完整分析 · 云端回答格式异常",
        "local_validation_failed": "本地完整分析 · 云端回答校验未通过",
    }
    return labels.get(degraded_reason, "本地完整分析")


def degradation_warning(degraded_reason: str | None) -> str:
    if not degraded_reason:
        return ""
    reason_text = {
        _MISSING_CREDENTIAL_REASON: "未配置 AI 服务。",
        "insufficient_quota": "云端 AI 服务余额或额度不足。",
        "invalid_credentials": "API Key 无效或无权限。",
        "rate_limited": "网络或 AI 服务出现短暂异常。",
        "network_error": "网络或 AI 服务出现短暂异常。",
        "timeout": "网络或 AI 服务出现短暂异常。",
        "service_unavailable": "网络或 AI 服务出现短暂异常。",
        "unparseable_response": "云端 AI 回答格式异常。",
        "local_validation_failed": "云端回答未通过本地四柱规则校验。",
    }.get(degraded_reason, "云端 AI 服务暂时不可用。")
    return (
        f"{reason_text}当前已切换为本地四柱规则完整分析。"
        "该回应可能不如云端 AI 分析全面。"
    )


def _chart_session_fingerprint(chart: dict) -> str:
    existing = chart.get("chart_fingerprint_v2")
    if existing:
        return str(existing)
    pillars = chart.get("pillars", {}) or {}
    values = [
        str((pillars.get(key, {}) or {}).get("pillar", ""))
        for key in ("year", "month", "day", "hour")
    ]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode("utf-8")).hexdigest()


def _render_supporting_details(item: dict) -> None:
    details = item.get("details", {}) or {}
    chart_evidence = details.get("chart_evidence", [])
    rule_evidence = details.get("rule_evidence", [])
    uncertainty = details.get("uncertainty", [])
    if not any((
        chart_evidence,
        rule_evidence,
        uncertainty,
    )):
        return
    with st.expander("查看补充的机器校验明细", expanded=False):
        if chart_evidence:
            st.markdown("**命盘证据**")
            for text in chart_evidence:
                st.write(f"• {text}")
        if rule_evidence:
            st.markdown("**规则依据**")
            for text in rule_evidence:
                st.write(f"• {text}")
        if uncertainty:
            st.markdown("**不确定性**")
            for text in uncertainty:
                st.write(f"• {text}")


def _render_message(item: dict) -> None:
    role = item.get("role", "assistant")
    with st.chat_message(role):
        details = item.get("details", {}) or {}
        sections = details.get("sections", {})
        if role == "assistant":
            has_structured_sections = isinstance(sections, dict) and bool(sections)
            degraded_reason = details.get("degraded_reason")
            warning = degradation_warning(degraded_reason)
            if warning:
                st.warning(warning)
            if has_structured_sections:
                for title in SIX_SECTION_TITLES:
                    content = sections.get(title)
                    if content:
                        st.markdown(f"### {title}")
                        st.write(content)
            else:
                st.markdown(str(item.get("content", "")))
            st.caption(
                answer_source_label(
                    str(item.get("source", "local_rules")),
                    degraded_reason,
                )
            )
            if not has_structured_sections:
                _render_supporting_details(item)
        else:
            st.markdown(str(item.get("content", "")))


def _save_answer(state, result: AnswerResult) -> None:
    append_chat_message(
        state,
        "assistant",
        result.answer,
        source=result.source,
        details={
            "chart_evidence": list(result.chart_evidence),
            "rule_evidence": list(result.rule_evidence),
            "timing_conditions": list(result.timing_conditions),
            "practical_advice": list(result.practical_advice),
            "uncertainty": list(result.uncertainty),
            "sections": dict(result.sections),
            "degraded_reason": result.degraded_reason,
        },
    )


def _answer(chart: dict, question: str) -> None:
    valid, error = validate_question(question)
    if not valid:
        st.warning(error)
        return
    text = question.strip()
    history = recent_context_messages(st.session_state)
    category = classify_question(text).category
    config = _runtime_ai_config()
    model_alias = (
        f"{config.provider}:{config.model}" if config.enabled else "local"
    )
    log_ai_event(
        event_code="AI_QA_REQUESTED",
        category=category,
        model_alias=model_alias,
    )
    append_chat_message(st.session_state, "user", text)
    started = time.monotonic()
    try:
        with st.spinner("正在根据本地四柱规则整理回答…"):
            result = answer_question(chart, text, history, config=config)
    except Exception:
        log_ai_event(
            event_code="AI_QA_FALLBACK",
            category=category,
            model_alias=model_alias,
            latency_ms=(time.monotonic() - started) * 1000,
            reason_code="unexpected_error",
        )
        st.error("本次回答未能完成，请稍后再试。")
        return
    _save_answer(st.session_state, result)
    elapsed = (time.monotonic() - started) * 1000
    if result.source == "cloud_validated":
        log_ai_event(
            event_code="AI_QA_VALIDATED",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
        )
    else:
        log_ai_event(
            event_code="AI_QA_FALLBACK",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
            reason_code=result.degraded_reason,
        )
    touch_private_session(st.session_state)
    _render_message(st.session_state[CHAT_MESSAGES_KEY][-1])


def render_inquiry_page() -> None:
    """Render the customer-facing Bazi AI chat."""
    chart = st.session_state.get("current_chart")
    if not chart:
        st.title("AI问答")
        st.info("请先新建或选择一个命盘，AI 问答才能读取本地四柱规则结论。")
        if st.button("新建命盘", type="primary"):
            st.session_state["navigate_to"] = "新建命盘"
            st.rerun()
        return
    if chart.get("error"):
        st.error("当前命盘未能完整生成，请重新排盘。")
        return

    expire_chat_session(st.session_state)
    switched = initialize_chat_for_chart(st.session_state, _chart_session_fingerprint(chart))
    if switched:
        log_ai_event(event_code="AI_QA_CLEARED", reason_code="profile_switch")

    st.markdown(
        """
        <section class="v106c-page-hero">
          <div class="v106c-page-eyebrow">LOCAL RULES · AI Q&amp;A</div>
          <div class="v106c-page-title">AI问答</div>
          <div class="v106c-page-subtitle">用当前命盘的本地四柱事实回答，并显示依据与不确定性。</div>
        </section>
        <div class="ms-report-panel">
          <span class="ms-mini-metric">对话最多保留 20 条</span>
          <span class="ms-tag">本地规则校验</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_loaded_profile_hint(st.session_state.get("current_profile", {}), chart)
    st.caption("AI 不能确认现实婚姻状态，也不会保证投资结果。")
    st.info("无需在问答中输入姓名或重复输入出生资料。请直接询问希望了解的命理主题。")

    with st.expander("当前命盘的本地规则摘要", expanded=False):
        render_rule_summary(chart)

    if st.button("清空对话", use_container_width=False):
        clear_chat_session(st.session_state)
        initialize_chat_for_chart(st.session_state, _chart_session_fingerprint(chart))
        log_ai_event(event_code="AI_QA_CLEARED", reason_code="user_clear")
        st.success("本次对话已清空。")
        st.rerun()

    for item in st.session_state.get(CHAT_MESSAGES_KEY, []):
        _render_message(item)

    st.markdown("#### 你可以这样问")
    columns = st.columns(2)
    suggested = None
    for index, prompt in enumerate(SUGGESTED_QUESTIONS):
        with columns[index % 2]:
            if st.button(prompt, key=f"ai_suggestion_{index}", use_container_width=True):
                suggested = prompt

    typed = st.chat_input("请输入关于强弱、格局、财运、事业、姻缘或流年的问题（最多 500 字）")
    question = suggested or typed
    if question is not None:
        _answer(chart, question)
