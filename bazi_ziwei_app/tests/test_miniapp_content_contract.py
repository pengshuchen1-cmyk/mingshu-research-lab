from pathlib import Path


CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "miniapp"
    / "round-two-content-contract.md"
)
ACCEPTANCE = (
    Path(__file__).resolve().parents[1]
    / "acceptance_samples"
    / "round_three_finalization_acceptance.md"
)


def test_round_two_contract_maps_every_approved_component_to_page_fields_and_action():
    text = CONTRACT.read_text(encoding="utf-8")

    for component in [
        "Hero",
        "DailyAdvice",
        "AnnualOverview",
        "RiskAction",
        "MonthCard",
        "EventDisclosure",
        "FourPillarsMatrix",
        "ElementDistribution",
        "FiveDimensionInsight",
        "UnifiedProfileForm",
        "ProfileStatus",
    ]:
        assert f"| `{component}` |" in text

    assert "小程序页面" in text
    assert "字段语义" in text
    assert "动作" in text
    assert "/pages/today/index" in text
    assert "/pages/chart/index" in text
    assert "/pages/yearly/index" in text
    assert "/pages/profile/edit/index" in text


def test_round_two_contract_defines_shared_client_boundaries():
    text = CONTRACT.read_text(encoding="utf-8")

    for token in [
        "activeMonthIndex",
        "number | null",
        "默认值为 `null`",
        "一次只展开一个月",
        "JSON",
        "可序列化",
        "隐私",
        "脱敏",
        "空态",
        "百分比",
        "偏旺",
        "需观察",
        "不复制算法",
    ]:
        assert token in text


def test_profile_contract_matches_the_safe_presentation_model_fields():
    text = CONTRACT.read_text(encoding="utf-8")

    for required in [
        "profile_status.has_profile",
        "profile_status.has_chart",
        "profile_status.next_action",
        "chart_summary.ready",
        "chart_summary.summary",
    ]:
        assert required in text

    for forbidden in [
        "profile_status.established",
        "profile_status.display_name",
        "ProfileStatus.display_name",
        "updated_at",
    ]:
        assert forbidden not in text


def test_round_three_contract_defines_identity_terms_and_full_dimension_views():
    text = CONTRACT.read_text(encoding="utf-8")

    for component in [
        "PersonalIdentityCard",
        "TermChip",
        "TermDetail",
        "FiveDimensionInsight",
    ]:
        assert f"| `{component}` |" in text

    for required_field in [
        "day_master/day_element/strength/dominant_elements/pattern/summary/term_ids",
        "term_id/label/group/accessibility_label",
        "term_id/label/definition/observation_scope/boundary/personalized",
        "key/label/score/level/summary/detail_label/evidence/strengths/risks/advice",
    ]:
        assert required_field in text

    assert "完整正文" in text
    assert "不得截断" in text


def test_round_three_contract_keeps_one_active_term_and_server_owned_calculations():
    text = CONTRACT.read_text(encoding="utf-8")

    for token in [
        "activeTermId: string | null",
        "一次只展开一个术语",
        "再次点击当前术语时恢复 `null`",
        "十神",
        "强弱",
        "喜忌",
        "relationship_signature",
        "客户端不得计算",
        "服务端展示模型",
    ]:
        assert token in text


def test_round_three_contract_excludes_sources_and_raw_profile_data_from_outputs_and_logs():
    text = CONTRACT.read_text(encoding="utf-8")

    for token in [
        "公开展示响应采用字段白名单",
        "不得返回 `source_titles`",
        "内部展示 API 响应",
        "错误日志",
        "分析埋点",
        "姓名、出生日期、出生时辰、出生地点",
        "原始资料仅存在于用户主动提交的排盘请求",
        "请求完成后不得写入日志或缓存键",
    ]:
        assert token in text


def test_round_three_acceptance_covers_breakpoints_focus_touch_and_overflow():
    text = ACCEPTANCE.read_text(encoding="utf-8")

    for viewport in ["375px", "768px", "1024px", "1440px"]:
        assert viewport in text
    for area in ["个人摘要", "术语点击", "五维全文", "关系详情", "命理依据"]:
        assert area in text
    for token in [
        "Tab 顺序",
        "可见焦点",
        "44px",
        "8px",
        "横向溢出",
        "正文不低于 16px",
        "不依赖颜色",
    ]:
        assert token in text


def test_round_three_contract_names_real_public_projection_and_pending_browser_gate():
    contract = CONTRACT.read_text(encoding="utf-8")
    acceptance = ACCEPTANCE.read_text(encoding="utf-8")

    for function_name in [
        "build_chart_public_view",
        "build_personal_identity_card_view",
        "build_term_chip_view",
        "build_term_detail_view",
        "build_five_dimension_insight_view",
        "build_term_disclosure_semantics",
        "transition_term_disclosure",
    ]:
        assert function_name in contract
    assert "网页内部身份卡仍可保留姓名" in contract
    assert "内部核心结果不被投影函数修改" in contract
    assert "自动化已通过" in acceptance
    assert "真实浏览器待主代理验收" in acceptance
    assert "scrollWidth <= clientWidth" in acceptance
