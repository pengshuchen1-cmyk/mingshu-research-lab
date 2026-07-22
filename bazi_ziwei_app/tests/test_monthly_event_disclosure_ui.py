from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _enhanced_month(**overrides):
    month = {
        "month": 3,
        "month_name": "三月",
        "pillar": "庚辰",
        "relation": "忌神相关",
        "direction": "先稳住节奏，再根据现实进展调整。",
        "has_clash": True,
    }
    month.update(overrides)
    return month


def _event(label, **overrides):
    event = {
        "event_type": "contract_document",
        "label": label,
        "probability_level": "较高",
        "score": 72,
        "plain_summary": "合同、审批与书面确认会成为本月重点。",
        "reason": "现实中容易遇到资料补充、条款复核或流程确认。",
        "real_world_signals": ["合同条款", "审批流程"],
        "trigger_factors": ["正官被引动", "月支冲动"],
        "user_visible_basis": "规则与文书主题受流月触发，需要结合现实进展复核。",
        "basis": "内部详细依据。",
        "advice": "重要内容落到文字，提交前再核对一次。",
        "source_ids": ["sanming_tonghui"],
    }
    event.update(overrides)
    return event


def test_build_month_card_view_exposes_only_readable_month_and_event_fields():
    from ui.yearly_page import build_month_card_view

    result = build_month_card_view(
        _enhanced_month(),
        {
            "top_events": [
                _event("合同文书"),
                _event("资料审批", probability_level="中等"),
                _event("流程复核", probability_level="需观察"),
                _event("不应出现的第四项"),
            ]
        },
    )

    assert set(result) == {
        "month_name",
        "pillar",
        "status",
        "direction",
        "event_tags",
        "events",
    }
    assert result["month_name"] == "三月"
    assert result["pillar"] == "庚辰"
    assert "忌神相关" in result["status"]
    assert "变动" in result["status"]
    assert result["direction"] == "先稳住节奏，再根据现实进展调整。"
    assert result["event_tags"] == ["合同文书", "资料审批", "流程复核"]
    assert len(result["events"]) == 3

    first = result["events"][0]
    assert set(first) == {
        "title",
        "probability",
        "summary",
        "reality",
        "triggers",
        "basis",
        "advice",
    }
    assert first == {
        "title": "合同文书",
        "probability": "较高",
        "summary": "合同、审批与书面确认会成为本月重点。",
        "reality": "现实中容易遇到资料补充、条款复核或流程确认。",
        "triggers": ["正官被引动", "月支冲动"],
        "basis": "规则与文书主题受流月触发，需要结合现实进展复核。",
        "advice": "重要内容落到文字，提交前再核对一次。",
    }

    visible_text = repr(result)
    for forbidden in ["event_type", "score", "source_ids", "sanming_tonghui"]:
        assert forbidden not in visible_text


def test_build_month_card_view_uses_readable_fallbacks_for_sparse_events():
    from ui.yearly_page import build_month_card_view

    result = build_month_card_view(
        _enhanced_month(has_clash=False, relation="平稳观察", direction=""),
        {
            "basis": "本月合并依据。",
            "top_events": [
                {
                    "label": "进展待确认",
                    "probability_level": "需观察",
                    "trigger_factors": [],
                }
            ],
        },
    )

    event = result["events"][0]
    assert result["status"] == "平稳观察"
    assert result["direction"] == "按现实进展稳步推进，为调整保留余量。"
    assert event["summary"]
    assert event["reality"]
    assert event["basis"] == "本月合并依据。"
    assert event["advice"]


def test_build_month_card_view_returns_a_readable_empty_state():
    from ui.yearly_page import build_month_card_view

    result = build_month_card_view(_enhanced_month(), {"top_events": []})

    assert result["event_tags"] == []
    assert len(result["events"]) == 1
    empty = result["events"][0]
    assert empty["title"] == "本月暂无明确重点事件"
    assert empty["probability"] == "需观察"
    assert "现实进展" in empty["summary"]
    assert empty["advice"]


def test_build_month_card_view_uses_real_bridge_evidence_when_trigger_factors_are_absent():
    from core.monthly_engine import analyze_monthly_fortune
    from core.yearly_engine import analyze_yearly_fortune
    from ui.yearly_page import build_month_card_view, build_monthly_event_results

    chart = {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
            "month": {"gan": "丙", "zhi": "寅", "pillar": "丙寅"},
            "day": {"gan": "甲", "zhi": "午", "pillar": "甲午"},
            "hour": {"gan": "庚", "zhi": "申", "pillar": "庚申"},
        },
        "five_elements": {"木": 3.0, "火": 2.0, "土": 1.0, "金": 2.0, "水": 1.0},
        "ten_god_counts": {"比肩": 2, "食神": 1, "七杀": 1, "偏印": 1},
        "day_master_strength": {
            "strength": "中和",
            "net_score": 1.0,
            "favorable_elements": ["木", "火"],
            "unfavorable_elements": ["金", "水"],
        },
    }
    monthly_data = analyze_monthly_fortune(chart, 2026)
    yearly_data = analyze_yearly_fortune(chart, 2026)
    results = build_monthly_event_results(chart, monthly_data, yearly_data, None)
    bridge_event = next(
        event
        for result in results
        for event in result.get("top_events", [])
        if event.get("from_bridge")
        and not event.get("trigger_factors")
        and event.get("evidence")
    )
    expected = [
        item["detail"]
        for item in bridge_event["evidence"]
        if isinstance(item, dict) and item.get("detail")
    ][:3]

    view = build_month_card_view(_enhanced_month(), {"top_events": [bridge_event]})

    assert expected
    assert view["events"][0]["triggers"] == [
        "相关命盘主题被流月引动",
        "流月五行关系被引动",
        "原局结构提供相关线索",
    ]
    for forbidden in [
        "source_ids",
        "event_type",
        "score",
        "{'type'",
        "[{'type'",
        "family_expense",
        "peer",
    ]:
        assert forbidden not in repr(view)


def test_build_month_card_view_safely_reads_a_single_evidence_mapping():
    from ui.yearly_page import build_month_card_view

    bridge_event = _event("资料复核")
    bridge_event.pop("trigger_factors")
    bridge_event["evidence"] = {
        "detail": "官杀与月支规则主题被引动",
        "type": "is_officer_month",
        "source_ids": ["san_ming_tong_hui"],
    }

    view = build_month_card_view(_enhanced_month(), {"top_events": [bridge_event]})

    assert view["events"][0]["triggers"] == ["相关命盘主题被流月引动"]
    visible = repr(view)
    assert "is_officer_month" not in visible
    assert "san_ming_tong_hui" not in visible


def _master_case_context(pillars):
    return {
        "chart_pillars_year_month_day_hour": pillars,
        "target_year": 2026,
        "month_index": 1,
        "month_ten_god_group": "peer",
        "favorable_relation": "忌神相关",
        "clash_any": True,
        "activate_peach_blossom": True,
        "group_counts": {"peer": 2, "wealth": 1, "output": 1},
        "month_zhi": "寅",
        "month_zhi_element": "木",
    }


def test_master_case_reference_evidence_becomes_neutral_without_raw_sample_data():
    from core.monthly_event_activation_bridge import (
        activate_master_case_reference_candidates,
        load_activation_assets,
    )
    from ui.yearly_page import build_month_card_view

    candidates = activate_master_case_reference_candidates(
        _master_case_context(["己卯", "壬申", "乙未", "辛巳"]),
        load_activation_assets(),
    )
    candidate = candidates[0]
    assert candidate["evidence"][0]["type"] == "master_case_reference"
    assert candidate["evidence"][1]["type"] == "month_index"

    view = build_month_card_view(_enhanced_month(), {"top_events": [candidate]})

    triggers = view["events"][0]["triggers"]
    assert triggers[:2] == [
        "历史样本规则提示相关主题需留意",
        "本月节奏位置触发相关提醒",
    ]
    visible = repr(view)
    for forbidden in [
        "2026_m",
        "month_index",
        "师傅原文",
        "注意3号、13号跟23号",
        "chen_pengshu_2026_master_monthly",
        "真实样本同段记录",
    ]:
        assert forbidden not in visible


def test_master_case_combination_evidence_hides_period_pattern_and_original_logic():
    from core.monthly_event_activation_bridge import (
        activate_master_case_combination_candidates,
        load_activation_assets,
    )
    from ui.yearly_page import build_month_card_view

    candidates = activate_master_case_combination_candidates(
        _master_case_context(["庚午", "己丑", "戊戌", "甲寅"]),
        load_activation_assets(),
    )
    candidate = candidates[0]
    assert [item["type"] for item in candidate["evidence"][:3]] == [
        "master_case_combination",
        "month_index",
        "combination_logic",
    ]

    view = build_month_card_view(_enhanced_month(), {"top_events": [candidate]})

    triggers = view["events"][0]["triggers"]
    assert triggers[:2] == [
        "多项结构信号同时出现",
        "本月节奏位置触发相关提醒",
    ]
    visible = repr(view)
    for forbidden in [
        "2026_m",
        "month_index",
        "师傅原文",
        "师傅样本把",
        "zhou_huimin_2026_master_monthly",
        "真实样本组合",
        "流月位于样本段",
    ]:
        assert forbidden not in visible


def test_unknown_evidence_is_skipped_while_whitelisted_copy_stays_readable():
    from ui.yearly_page import build_month_card_view

    event = _event("结构提醒")
    event.pop("trigger_factors")
    event["evidence"] = [
        {"type": "element", "label": "五行关系需要留意"},
        {
            "type": "private_sample_blob",
            "detail": "2026_m09 month_index 师傅原文 样本编号 A-42",
        },
    ]

    view = build_month_card_view(_enhanced_month(), {"top_events": [event]})

    assert view["events"][0]["triggers"] == ["五行关系需要留意"]
    visible = repr(view)
    for forbidden in ["2026_m", "month_index", "师傅原文", "A-42"]:
        assert forbidden not in visible


def test_month_timeline_renders_twelve_named_nodes_with_text_status(monkeypatch):
    from ui.yearly_page import _render_month_timeline

    rendered = []
    monkeypatch.setattr(
        "ui.yearly_page.st.markdown",
        lambda body, **kwargs: rendered.append(str(body)),
    )
    month_views = [
        {
            "month_name": f"{month}月",
            "pillar": "庚辰",
            "status": "平稳观察" if month % 2 else "喜用相关",
            "direction": "稳步推进",
            "event_tags": [],
            "events": [],
        }
        for month in range(1, 13)
    ]

    _render_month_timeline(month_views)

    html = "\n".join(rendered)
    assert "ms3-month-timeline" in html
    assert html.count('class="ms3-month-node"') == 12
    for month in range(1, 13):
        assert f"{month}月" in html
    assert "平稳观察" in html
    assert "喜用相关" in html


def test_month_card_is_collapsed_by_default_with_a_stable_touch_entry(monkeypatch):
    from ui.yearly_page import _render_month_card, build_month_card_view

    rendered = []
    buttons = []
    expanders = []
    session_state = {}

    def button(label, **kwargs):
        buttons.append((label, kwargs))
        return False

    def unexpected_expander(*args, **kwargs):
        expanders.append((args, kwargs))
        raise AssertionError("收起时不应渲染二级依据")

    monkeypatch.setattr("ui.yearly_page.st.session_state", session_state)
    monkeypatch.setattr("ui.yearly_page.st.button", button)
    monkeypatch.setattr("ui.yearly_page.st.expander", unexpected_expander)
    monkeypatch.setattr(
        "ui.yearly_page.st.markdown",
        lambda body, **kwargs: rendered.append(str(body)),
    )
    view = build_month_card_view(_enhanced_month(), {"top_events": [_event("合同文书")]})

    _render_month_card(view, 6)

    assert len(buttons) == 1
    label, kwargs = buttons[0]
    assert label == "查看重点事件"
    assert kwargs["key"] == "monthly-events-6"
    assert kwargs["use_container_width"] is True
    assert kwargs["on_click"].__name__ == "_toggle_active_month"
    assert kwargs["args"] == (6,)
    assert "value" not in kwargs
    assert "monthly-events-6" not in session_state
    assert expanders == []
    html = "\n".join(rendered)
    assert "ms3-month-card" in html
    assert "三月" in html
    assert "庚辰" in html
    assert "现实表现" not in html


def test_expanded_month_card_groups_events_and_folds_basis(monkeypatch):
    from ui.yearly_page import _render_month_card, build_month_card_view

    rendered = []
    buttons = []
    expander_calls = []

    class _Context:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        "ui.yearly_page.st.session_state",
        {"ms3_active_month_index": 2},
    )
    monkeypatch.setattr(
        "ui.yearly_page.st.button",
        lambda label, **kwargs: buttons.append((label, kwargs)) or False,
    )
    monkeypatch.setattr(
        "ui.yearly_page.st.markdown",
        lambda body, **kwargs: rendered.append(str(body)),
    )

    def expander(label, **kwargs):
        expander_calls.append((label, kwargs))
        return _Context()

    monkeypatch.setattr("ui.yearly_page.st.expander", expander)
    view = build_month_card_view(_enhanced_month(), {"top_events": [_event("合同文书")]})

    _render_month_card(view, 2)

    assert buttons[0][0] == "收起重点事件"
    html = "\n".join(rendered)
    for token in [
        "ms3-month-event",
        "合同文书",
        "较高",
        "一句话",
        "现实表现",
        "触发因素",
        "行动建议",
        "合同、审批与书面确认会成为本月重点。",
    ]:
        assert token in html
    assert expander_calls == [
        ("依据简写｜合同文书", {"expanded": False})
    ]
    assert "规则与文书主题受流月触发" in html
    for forbidden in ["event_type", "score", "source_ids", "sanming_tonghui"]:
        assert forbidden not in html


def test_month_disclosure_state_allows_only_one_active_month(monkeypatch):
    from ui.yearly_page import _toggle_active_month

    session_state = {}
    monkeypatch.setattr("ui.yearly_page.st.session_state", session_state)

    _toggle_active_month(3)
    assert session_state == {"ms3_active_month_index": 3}

    _toggle_active_month(8)
    assert session_state == {"ms3_active_month_index": 8}

    _toggle_active_month(8)
    assert session_state == {"ms3_active_month_index": None}


def test_monthly_section_source_removes_legacy_debug_table_and_event_emoji():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")

    for forbidden in [
        "流月事件差异化检查（开发调试）",
        "十二个月速览表",
        "📖",
        "🛠",
        "🔴",
        "🟡",
        "🟢",
        "💡",
        "💰",
        "🏠",
        "🚗",
        "📄",
        "💔",
        "🏥",
        "📌",
        "🔗",
        "📚",
    ]:
        assert forbidden not in source

    for required in [
        "build_month_card_view(enhanced_month, event_result)",
        "_render_month_timeline(month_views)",
        "_render_month_card(month_view, index)",
        'st.button(',
        "button_label",
        '"ms3_active_month_index"',
        '"\u6536\u8d77\u91cd\u70b9\u4e8b\u4ef6"',
        '"\u67e5\u770b\u91cd\u70b9\u4e8b\u4ef6"',
        'key=f"monthly-events-{index}"',
    ]:
        assert required in source
    assert "st.toggle(" not in source


def test_monthly_layout_uses_dedicated_two_column_container_and_mobile_single_column():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    monthly_section = source.split("# ====== 12个月流月卡与重点事件 ======", 1)[1]

    container_call = 'with st.container(key="ms3-month-grid"):'
    columns_call = "month_columns = st.columns(2)"
    render_call = "_render_month_card(month_view, index)"
    assert container_call in monthly_section
    assert columns_call in monthly_section
    assert monthly_section.index(container_call) < monthly_section.index(columns_call)
    assert monthly_section.index(columns_call) < monthly_section.index(render_call)

    for token in [
        ".ms3-month-timeline",
        ".ms3-month-node",
        ".ms3-month-card",
        ".ms3-month-event",
        "@media (max-width: 768px)",
        "min-height: 44px",
    ]:
        assert token in css

    mobile_css = css.split("@media (max-width: 768px)", 1)[1].split(
        "@media (max-width: 480px)", 1
    )[0]
    monthly_selector = '.st-key-ms3-month-grid [data-testid="stHorizontalBlock"] {'
    assert monthly_selector in mobile_css
    monthly_rule = mobile_css.split(monthly_selector, 1)[1].split("}", 1)[0]
    assert "display: grid !important" in monthly_rule
    assert "grid-template-columns: 1fr !important" in monthly_rule
    assert (
        '.stMain [data-testid="stHorizontalBlock"] > div {\n'
        "            flex: 1 1 100% !important;"
    ) not in css

    button_selector = ".stButton button {"
    assert button_selector in css
    button_rule = css.split(button_selector, 1)[1].split("}", 1)[0]
    assert "min-height: 44px" in button_rule
