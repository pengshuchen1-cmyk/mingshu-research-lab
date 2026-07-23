from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SECTION_TITLES = (
    "分析结论",
    "命盘依据",
    "规则依据",
    "阶段与触发条件",
    "现实建议",
    "不确定性与限制",
)


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class _FakeStreamlit:
    def __init__(self):
        self.warnings = []
        self.markdowns = []
        self.writes = []
        self.captions = []
        self.session_state = {}

    def chat_message(self, _role):
        return _Context()

    def warning(self, text):
        self.warnings.append(str(text))

    def markdown(self, text, **_kwargs):
        self.markdowns.append(str(text))

    def write(self, text):
        self.writes.append(str(text))

    def caption(self, text):
        self.captions.append(str(text))

    def expander(self, *_args, **_kwargs):
        return _Context()

    def spinner(self, *_args, **_kwargs):
        return _Context()


def test_ai_question_page_has_chat_controls_and_safe_limits():
    source = (ROOT / "ui" / "inquiry_page.py").read_text(encoding="utf-8")

    assert "st.chat_message" in source
    assert "st.chat_input" in source
    assert "清空对话" in source
    assert "validate_question" in source
    assert "render_rule_summary" in source
    assert "新建命盘" in source
    assert "repr(exc)" not in source
    assert "str(exc)" not in source
    assert "无需在问答中输入姓名或重复输入出生资料" in source


def test_assistant_message_renders_warning_and_all_six_sections_directly(monkeypatch):
    import ui.inquiry_page as inquiry_page

    fake = _FakeStreamlit()
    monkeypatch.setattr(inquiry_page, "st", fake)
    sections = {title: f"{title}内容" for title in SECTION_TITLES}

    inquiry_page._render_message(
        {
            "role": "assistant",
            "content": "不应依赖整段 Markdown",
            "source": "local_rules",
            "details": {
                "sections": sections,
                "degraded_reason": "network_error",
            },
        }
    )

    assert "网络或 AI 服务出现短暂异常" in fake.warnings[0]
    assert fake.markdowns == [f"### {title}" for title in SECTION_TITLES]
    assert fake.writes == [sections[title] for title in SECTION_TITLES]
    assert fake.captions == ["本地完整分析 · 网络或服务异常"]


def test_fallback_log_uses_exact_reason_code_without_content_or_pii(monkeypatch):
    import ui.inquiry_page as inquiry_page
    from core.ai_models import AnswerResult

    fake = _FakeStreamlit()
    events = []
    sections = {title: f"{title}内容" for title in SECTION_TITLES}
    result = AnswerResult(
        answer="回答正文",
        sections=sections,
        chart_evidence=("命盘证据",),
        rule_evidence=("规则证据",),
        timing_conditions=("阶段条件",),
        practical_advice=("现实建议",),
        uncertainty=("限制",),
        source="local_rules",
        degraded_reason="insufficient_quota",
    )
    monkeypatch.setattr(inquiry_page, "st", fake)
    monkeypatch.setattr(
        inquiry_page.AIConfig,
        "from_environment",
        classmethod(lambda cls: SimpleNamespace(enabled=True)),
    )
    monkeypatch.setattr(inquiry_page, "answer_question", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(inquiry_page, "log_ai_event", lambda **kwargs: events.append(kwargs))
    monkeypatch.setattr(inquiry_page, "touch_private_session", lambda _state: None)
    monkeypatch.setattr(inquiry_page, "_render_message", lambda _item: None)

    inquiry_page._answer(
        {"profile": {"name": "不应记录"}, "pillars": {}},
        "姓名：不应记录，出生于1990-01-01，问题正文",
    )

    fallback = next(item for item in events if item["event_code"] == "AI_QA_FALLBACK")
    assert fallback["reason_code"] == "insufficient_quota"
    assert set(fallback) == {
        "event_code",
        "category",
        "model_alias",
        "latency_ms",
        "reason_code",
    }
    assert "不应记录" not in repr(events)
    assert "1990-01-01" not in repr(events)


def test_privacy_center_discloses_deidentified_cloud_payload_and_exclusions():
    source = (ROOT / "ui" / "privacy_center_page.py").read_text(encoding="utf-8")
    notice = (
        "出生资料和排盘计算保留在本次会话；AI 问答会把去身份化命盘事实、"
        "问题和近期对话发送给已配置的云端 AI 服务。不会发送姓名、精确出生日期、"
        "出生地点或 API Key。"
    )
    assert notice in source


def test_ai_question_page_is_reachable_from_product_navigation():
    import app

    assert app.get_pages()["AI问答"].__name__ == "render_inquiry_page"
    assert ("问答", "AI问答") in app.PRODUCT_NAV_ITEMS
