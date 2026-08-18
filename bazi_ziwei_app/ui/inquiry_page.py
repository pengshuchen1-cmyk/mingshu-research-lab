"""Privacy-aware AI Q&A grounded in the local Four Pillars rule engine."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st

from core.ai_context import classify_question, redact_customer_text
from core.ai_models import (
    AIConfig,
    AnswerResult,
    ProgressStage,
    is_retryable_degradation,
)
from core.ai_orchestrator import answer_question
from core.ai_question_resolver import resolve_question
from core.ai_request_control import request_controller_for_config
from core.ai_session import (
    CHAT_MESSAGES_KEY,
    append_chat_message,
    expire_chat_session,
    initialize_chat_for_chart,
    previous_resolved_question,
    recent_context_messages,
    remember_dialogue_summary,
    validate_question,
)
from ui.bazi_components import render_loaded_profile_hint, render_rule_summary
from ui.primitives import empty_state_header, page_header
from utils.logger import log_ai_event
from utils.session_privacy import PENDING_INQUIRY_KEY, touch_private_session


SUGGESTED_QUESTIONS = (
    "请概括这个八字的强弱和格局，证据是什么？",
    "这个八字的财运和事业适合怎么发展？",
    "这个八字的姻缘桃花与婚姻建议是什么？",
    "未来一年需要重点注意什么？",
)
_MISSING_CREDENTIAL_REASON = "_".join(("missing", "api", "key"))
_AI_SESSION_ID_KEY = "bazi_ai_anonymous_session_id"
_SHANGHAI_TIMEZONE = ZoneInfo("Asia/Shanghai")
_PROGRESS_LABELS = {
    "validating_scope": "正在确认问题范围…",
    "resolving_question": "正在理解问题和时间…",
    "compiling_local_facts": "正在整理本地命盘事实…",
    "generating_cloud_answer": "Kimi 正在深入分析…",
    "validating_answer": "正在进行本地四柱规则校验…",
    "completed": "分析完成",
    "degraded": "已切换为本地完整分析",
    "rejected": "该问题超出四柱问答范围",
}


def _runtime_ai_config() -> AIConfig:
    try:
        secrets = st.secrets
    except (FileNotFoundError, RuntimeError):
        secrets = {}
    return AIConfig.from_environment(secrets)


def _anonymous_session_id(state) -> str:
    existing = state.get(_AI_SESSION_ID_KEY)
    if isinstance(existing, str) and existing:
        return existing
    value = uuid4().hex
    state[_AI_SESSION_ID_KEY] = value
    return value


def answer_source_label(
    source: str,
    degraded_reason: str | None,
    provider: str | None = None,
) -> str:
    if source == "cloud_validated":
        provider_name = {"kimi": "Kimi", "openai": "OpenAI"}.get(
            provider,
            "云端 AI",
        )
        return f"{provider_name} 云端分析 · 本地规则校验"
    labels = {
        _MISSING_CREDENTIAL_REASON: "本地完整分析 · 云端服务未配置",
        "insufficient_quota": "本地完整分析 · 云端额度不足",
        "invalid_credentials": "本地完整分析 · 云端认证异常",
        "rate_limited": "本地完整分析 · 网络或服务异常",
        "daily_budget": "本地完整分析 · 今日云端预算已用完",
        "duplicate_request": "本地完整分析 · 重复请求已拦截",
        "concurrency_limit": "本地完整分析 · 当前请求较多",
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
        "daily_budget": "今日云端 AI Token 预算已用完。",
        "duplicate_request": "检测到重复请求。",
        "concurrency_limit": "当前云端 AI 请求较多。",
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


def repair_notice(codes: tuple[str, ...] | list[str]) -> str:
    values = set(codes)
    if "CLOUD_UNKNOWN_CLAIM_ID" in values:
        return "部分云端段落引用异常，已按本地四柱规则替换。"
    if "CLOUD_ANSWER_TOO_LONG" in values:
        return "云端回答超过安全展示范围，已切换为本地完整分析。"
    if "CLOUD_SEGMENT_GUARD_ERROR" in values:
        return "云端段落校验出现异常，已切换为本地完整分析。"
    return ""


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


def _render_message(
    item: dict,
    *,
    retry_question: str = "",
    retry_key: str = "",
) -> bool:
    role = item.get("role", "assistant")
    with st.chat_message(role):
        details = item.get("details", {}) or {}
        if role == "assistant":
            degraded_reason = details.get("degraded_reason")
            warning = degradation_warning(degraded_reason)
            if warning:
                st.warning(warning)
            if item.get("source") == "cloud_validated":
                notice = repair_notice(details.get("violation_codes", []))
                if notice:
                    st.info(notice)
            interpretation_receipt = str(
                details.get("interpretation_receipt") or ""
            ).strip()
            if interpretation_receipt:
                st.caption(f"问题理解：{interpretation_receipt}")
            st.markdown(str(item.get("content", "")))
            st.caption(
                answer_source_label(
                    str(item.get("source", "local_rules")),
                    degraded_reason,
                    str(item.get("provider") or "") or None,
                )
            )
            _render_supporting_details(item)
            if retry_question:
                return st.button(
                    "重新获取云端详细分析",
                    key=retry_key,
                    use_container_width=False,
                )
        else:
            st.markdown(str(item.get("content", "")))
    return False


def _retry_question_for_message(messages: list[dict], index: int) -> str:
    if not 0 <= index < len(messages):
        return ""
    item = messages[index]
    if (
        not isinstance(item, dict)
        or item.get("role") != "assistant"
        or item.get("source") != "local_rules"
    ):
        return ""
    details = item.get("details", {}) or {}
    if (
        not isinstance(details, dict)
        or details.get("retryable") is not True
        or not is_retryable_degradation(details.get("degraded_reason"))
    ):
        return ""
    request_id = str(item.get("request_id") or "")
    if not request_id:
        return ""
    for candidate in reversed(messages[:index]):
        if (
            isinstance(candidate, dict)
            and candidate.get("role") == "user"
            and candidate.get("request_id") == request_id
        ):
            return str(candidate.get("content") or "").strip()
    return ""


def _save_answer(
    state,
    result: AnswerResult,
    *,
    request_id: str = "",
) -> None:
    append_chat_message(
        state,
        "assistant",
        result.answer,
        source=result.source,
        provider=result.provider,
        request_id=result.request_id or request_id,
        details={
            "chart_evidence": list(result.chart_evidence),
            "rule_evidence": list(result.rule_evidence),
            "timing_conditions": list(result.timing_conditions),
            "practical_advice": list(result.practical_advice),
            "uncertainty": list(result.uncertainty),
            "degraded_reason": result.degraded_reason,
            "interpretation_receipt": result.interpretation_receipt,
            "retryable": result.retryable,
            "violation_codes": list(result.violation_codes),
        },
    )


def _answer(chart: dict, question: str) -> bool:
    valid, error = validate_question(question)
    if not valid:
        st.warning(error)
        return False
    text = question.strip()
    history = recent_context_messages(st.session_state)
    now = datetime.now(_SHANGHAI_TIMEZONE)
    previous = previous_resolved_question(st.session_state)
    resolved = resolve_question(
        redact_customer_text(text, max_input_chars=2000),
        now=now,
        previous=previous,
    )
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
    started = time.monotonic()
    request_id = uuid4().hex
    append_chat_message(
        st.session_state,
        "user",
        text,
        request_id=request_id,
    )
    # Streamlit executes the model call synchronously. Render the saved user
    # message in this run so it is visible while the status widget is active;
    # the normal rerun will then place it back in the canonical thread order.
    _render_message(st.session_state[CHAT_MESSAGES_KEY][-1])
    status = st.status("正在理解问题…", expanded=True)

    def on_progress(stage: ProgressStage) -> None:
        terminal = stage in {"completed", "degraded", "rejected"}
        state = (
            "complete"
            if stage == "completed"
            else "error"
            if terminal
            else "running"
        )
        status.update(
            label=_PROGRESS_LABELS[stage],
            state=state,
            expanded=not terminal,
        )

    try:
        with status:
            result = answer_question(
                chart,
                text,
                history,
                previous=previous,
                now=now,
                config=config,
                on_progress=on_progress,
                request_controller=request_controller_for_config(config),
                session_id=_anonymous_session_id(st.session_state),
                request_id=request_id,
            )
    except Exception:
        status.update(
            label="本次回答未能完成",
            state="error",
            expanded=False,
        )
        log_ai_event(
            event_code="AI_QA_FALLBACK",
            category=category,
            model_alias=model_alias,
            latency_ms=(time.monotonic() - started) * 1000,
            reason_code="unexpected_error",
        )
        st.error("本次回答未能完成，请稍后再试。")
        return False
    _save_answer(st.session_state, result, request_id=request_id)
    if result.source in {"cloud_validated", "local_rules"}:
        remember_dialogue_summary(st.session_state, resolved)
    elapsed = (time.monotonic() - started) * 1000
    if result.source == "cloud_validated":
        log_ai_event(
            event_code="AI_QA_VALIDATED",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
        )
    elif result.source == "boundary":
        log_ai_event(
            event_code="AI_QA_SCOPE_REJECTED",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
            reason_code="scope_rejected",
        )
    elif result.source == "clarification":
        log_ai_event(
            event_code="AI_QA_RETRY_REQUESTED",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
            reason_code="clarification_required",
        )
    else:
        log_ai_event(
            event_code="AI_QA_FALLBACK",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
            reason_code=result.degraded_reason,
        )
    for violation_code in result.violation_codes:
        log_ai_event(
            event_code="AI_QA_SEGMENT_REPLACED",
            category=category,
            model_alias=model_alias,
            latency_ms=elapsed,
            violation_code=violation_code,
        )
    touch_private_session(st.session_state)
    return True


PENDING_QUESTION_KEY = PENDING_INQUIRY_KEY


def pop_pending_question(state) -> str | None:
    """Consume a session-only homepage handoff without bypassing validation."""
    pending = str(state.pop(PENDING_QUESTION_KEY, "") or "").strip()
    return pending or None


def render_inquiry_page() -> None:
    """Render the customer-facing Bazi AI chat."""
    chart = st.session_state.get("current_chart")
    if not chart:
        empty_state_header(
            "AI 问答需要个人命盘",
            "请先新建或选择一个命盘，AI 才能读取本地四柱规则结论。",
        )
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

    with st.container(key="ms-inquiry-page"):
        page_header(
            "命理助手",
            "本地规则校验 · 对话最多保留 20 条",
            eyebrow="AI CHAT",
        )

        with st.container(key="ms-inquiry-context"):
            render_loaded_profile_hint(st.session_state.get("current_profile", {}), chart)
            with st.expander("当前命盘的本地规则摘要", expanded=False):
                render_rule_summary(chart)
            st.markdown(
                '<p class="ms-inquiry-safety">无需重复输入姓名或出生资料。'
                '内容仅作传统文化参考，不替代现实中的医疗、法律或投资判断。</p>',
                unsafe_allow_html=True,
            )

        messages = list(st.session_state.get(CHAT_MESSAGES_KEY, []))
        with st.container(key="ms-inquiry-thread"):
            for index, item in enumerate(messages):
                retry_question = _retry_question_for_message(messages, index)
                retry_requested = _render_message(
                    item,
                    retry_question=retry_question,
                    retry_key=f"ai_retry_{item.get('request_id', index)}_{index}",
                )
                if retry_requested:
                    if _answer(chart, retry_question):
                        st.rerun()

            if not messages:
                st.markdown(
                    """
                    <div class="ms-inquiry-empty">
                      <strong>从你真正关心的问题开始</strong>
                      <span>可以询问命盘结构、事业财运、关系主题或阶段趋势。</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    typed = st.chat_input(
        "输入你想了解的命理问题",
        key="ms_inquiry_chat_input",
        max_chars=2000,
    )
    pending = pop_pending_question(st.session_state)
    question = pending or typed
    if question is not None and _answer(chart, question):
        st.rerun()
