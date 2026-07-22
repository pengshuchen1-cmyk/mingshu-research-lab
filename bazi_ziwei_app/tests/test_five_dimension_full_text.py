"""五维洞察完整文本与详情展示回归测试。"""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _long_summary(label: str) -> str:
    return (
        f"{label}核心简评必须完整保留命盘中的具体信息、现实边界和行动节奏，"
        "不能为了让卡片看起来等高而截断正文。这段内容特意超过七十二个字符，"
        "后半段继续说明长期观察、阶段复盘与现实验证，确保桌面和手机都能逐字阅读。"
    )


def _dimension_payload() -> tuple[dict, dict[str, str]]:
    summaries = {
        "财富": _long_summary("财富"),
        "关系": _long_summary("关系"),
        "健康": _long_summary("健康"),
        "事业": _long_summary("事业"),
    }
    return (
        {
            "scores": {
                "wealth": 71,
                "romance": 68,
                "health_stability": 43,
                "career": 82,
                "overall_balance": 66,
            },
            "wealth_overview": {
                "wealth_summary": summaries["财富"],
                "wealth_opportunities": ["财富优势：技能可形成稳定收益入口"],
                "wealth_risks": ["财富隐患：合作消耗需要设定边界"],
                "money_management_advice": "财富建议：先保护现金流并预留缓冲。",
                "evidence": ["财富证据：财星与食伤均有明确落点"],
            },
            "romance_overview": {
                "romance_summary": summaries["关系"],
                "relationship_strengths": ["关系优势：重视现实基础和稳定性"],
                "relationship_risks": ["关系隐患：双方边界需要持续协调"],
                "communication_advice": "关系建议：把感受、计划和责任分别说清。",
                "evidence": ["关系证据：夫妻宫与配偶星均有可核对信息"],
            },
            "health_overview": {
                "health_summary": summaries["健康"],
                "health_strengths": ["健康优势：五行结构仍有恢复支点"],
                "lifestyle_risks": ["健康隐患：高压阶段容易透支恢复节奏"],
                "long_term_care_advice": ["健康建议：规律作息并结合体检观察。"],
                "evidence": ["健康证据：日主状态与五行强弱可核对"],
            },
            "career_overview": {
                "career_summary": summaries["事业"],
                "career_strengths": ["事业优势：表达和创造能力较突出"],
                "career_risks": ["事业隐患：协作分工需要明确"],
                "long_term_action_advice": ["事业建议：先积累可迁移能力。"],
                "evidence": ["事业证据：十神结构与日主状态均有记录"],
            },
            "score_details": {
                "overall_pace": {
                    "advice": ["整体建议：按四项表现安排节奏，不以单项替代现实判断。"]
                }
            },
        },
        summaries,
    )


def test_four_core_dimension_summaries_are_rendered_in_full(monkeypatch):
    import ui.life_overview_page as page

    payload, summaries = _dimension_payload()
    markdown_calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        page.st,
        "markdown",
        lambda body, **kwargs: markdown_calls.append((str(body), kwargs)),
    )
    monkeypatch.setattr(page.st, "expander", lambda *_args, **_kwargs: nullcontext())

    page._render_five_dimension_insights(payload)

    card_html = "\n".join(
        body for body, kwargs in markdown_calls if kwargs.get("unsafe_allow_html")
    )
    for summary in summaries.values():
        assert summary in card_html
    assert "…" not in card_html


def test_each_core_dimension_detail_uses_real_fields_without_repeating_summary(monkeypatch):
    import ui.life_overview_page as page

    payload, summaries = _dimension_payload()
    markdown_calls: list[str] = []
    expander_labels: list[str] = []

    def expander(label, **_kwargs):
        expander_labels.append(str(label))
        return nullcontext()

    monkeypatch.setattr(
        page.st,
        "markdown",
        lambda body, **_kwargs: markdown_calls.append(str(body)),
    )
    monkeypatch.setattr(page.st, "expander", expander)

    page._render_five_dimension_insights(payload)

    rendered = "\n".join(markdown_calls)
    for label in ("财富", "关系", "健康", "事业"):
        assert f"查看详情：{label}" in expander_labels
        for section in ("证据", "优势", "隐患", "建议"):
            assert f"{label}{section}" in rendered
        assert rendered.count(summaries[label]) == 1


def test_overall_balance_detail_only_summarizes_four_core_dimensions():
    import ui.life_overview_page as page

    payload, _summaries = _dimension_payload()
    payload["evidence"] = ["不应被整体平衡当作独立证据"]

    balance = page._build_dimension_views(payload)[-1]

    assert balance["label"] == "整体平衡"
    assert balance["detail_label"] == "四项结构"
    assert balance["evidence"] == [
        "财富 71 分（中上）",
        "关系 68 分（中上）",
        "健康 43 分（需经营）",
        "事业 82 分（偏强）",
    ]
    assert "不应被整体平衡当作独立证据" not in str(balance)


def test_overall_balance_describes_all_equal_scores_as_balanced():
    import ui.life_overview_page as page

    balance = page._build_dimension_views(
        {
            "scores": {
                "wealth": 60,
                "romance": 60,
                "health_stability": 60,
                "career": 60,
                "overall_balance": 60,
            }
        }
    )[-1]

    conclusion = "".join(balance["strengths"] + balance["risks"])
    assert "四项表现相对均衡" in conclusion
    assert "相对较高项" not in conclusion
    assert "相对需要经营" not in conclusion


def test_overall_balance_lists_every_tied_highest_and_lowest_dimension():
    import ui.life_overview_page as page

    balance = page._build_dimension_views(
        {
            "scores": {
                "wealth": 80,
                "romance": 80,
                "health_stability": 40,
                "career": 40,
                "overall_balance": 60,
            }
        }
    )[-1]

    conclusion = "".join(balance["strengths"] + balance["risks"])
    assert "并列最高项为财富、关系" in conclusion
    assert "并列最低项为健康、事业" in conclusion
    for label in ("财富", "关系", "健康", "事业"):
        assert conclusion.count(label) == 1


def test_dimension_grid_reflows_three_two_one_without_mobile_overflow():
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in styles
    assert "@media (max-width: 1024px)" in styles
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in styles
    assert "@media (max-width: 640px)" in styles
    assert ".ms4-dimension-grid { grid-template-columns: 1fr; }" in styles
    assert "overflow-wrap: anywhere" in styles
    assert ".ms4-dimension-summary" in styles
    assert "font-size: 16px" in styles


def test_dimension_views_expose_stable_public_keys_in_reading_order():
    import ui.life_overview_page as page

    payload, _summaries = _dimension_payload()

    assert [item["key"] for item in page._build_dimension_views(payload)] == [
        "wealth",
        "relationship",
        "health",
        "career",
        "overall_balance",
    ]
