"""40 命例、780 对比较的本地差异性审计规则。"""

from __future__ import annotations

import time


def test_similarity_metrics_are_deterministic_and_ignore_sample_identifiers():
    from core.diversity_audit import compare_texts, normalize_personalized_text

    left = "样例-001｜甲木日主，适合先整理资源，再推进合作。"
    right = "样例-039｜甲木日主，适合先整理资源，再推进合作。"
    distinct = "辛金日主，本阶段先收紧预算并复核合同边界。"

    assert normalize_personalized_text(left) == normalize_personalized_text(right)
    assert compare_texts(left, right)["score"] == 1.0
    assert compare_texts(left, distinct)["score"] < 0.7


def test_identity_audit_excludes_shared_term_definitions_but_keeps_personalization():
    from core.diversity_audit import build_identity_audit_text

    text = build_identity_audit_text(
        {"summary": "甲木日主，先看结构。", "pattern": "正官格"},
        [
            {
                "term_id": "direct-officer",
                "definition": "这是所有用户共用的大众术语定义。",
                "observation_scope": "共用观察范围。",
                "personalized": {"count": 2, "interpretation": "本盘官星落在月柱与时柱。"},
            }
        ],
    )

    assert "大众术语定义" not in text
    assert "共用观察范围" not in text
    assert "甲木日主" in text
    assert "本盘官星落在月柱与时柱" in text


def test_monthly_audit_uses_user_visible_content_not_internal_score_maps():
    from core.diversity_audit import build_monthly_audit_text

    text = build_monthly_audit_text(
        [{"month": 1, "month_name": "一月", "pillar": "丙寅", "theme": "先处理合同"}],
        [
            {
                "month": 1,
                "basis": "本月官星与月支共同触发。",
                "event_score_map": {"secret_internal_event": 99},
                "bridge_events": [{"case_id": "private-rule-id"}],
                "top_events": [
                    {
                        "event_type": "contract_document",
                        "label": "合同文书",
                        "one_line": "合同确认更值得留意。",
                        "reason": "条款与责任边界被引动。",
                        "risk_points": ["只听口头承诺"],
                        "advice": "重要内容写下来。",
                        "basis": "官星与文书主题相关。",
                        "evidence": [{"type": "internal", "case_id": "hidden"}],
                    }
                ],
            }
        ],
    )

    for visible in ("一月", "丙寅", "合同文书", "条款与责任边界", "只听口头承诺", "重要内容写下来"):
        assert visible in text
    for internal in ("secret_internal_event", "private-rule-id", "case_id", "hidden"):
        assert internal not in text


def test_audit_text_keeps_meaningful_numeric_scores():
    from core.diversity_audit import joined_audit_text

    assert "score=62" in joined_audit_text({"label": "财富", "score": 62})


def test_similarity_metric_handles_long_reports_within_audit_budget():
    from core.diversity_audit import compare_texts

    left = "".join(f"第{index}段甲木日主需要整理资源与合作边界。" for index in range(800))
    right = "".join(f"第{index}段甲木日主需要整理资源与合同边界。" for index in range(800))
    started = time.perf_counter()
    result = compare_texts(left, right)

    assert time.perf_counter() - started < 0.5
    assert 0.0 <= result["score"] <= 1.0


def test_pairwise_section_audit_classifies_all_780_pairs():
    from core.diversity_audit import audit_section_texts

    texts = {f"样例-{index:03d}": f"日主结构{index}，行动建议{index % 7}" for index in range(1, 41)}
    result = audit_section_texts("演示板块", texts)

    assert result["pair_count"] == 780
    assert result["exact_duplicate_count"] == 0
    assert len(result["pairs"]) == 780
    assert 0.0 <= result["p95"] <= 1.0


def test_section_audit_downweights_corpus_wide_shared_boilerplate():
    from core.diversity_audit import audit_section_texts

    shared = "数量只是线索应连同强弱位置和现实经历一起理解" * 15
    texts = {
        f"样例-{index:03d}": shared + f"日主{index}结构落位{index * 17}行动抓手{index * 29}"
        for index in range(1, 41)
    }

    result = audit_section_texts("共享说明测试", texts)

    assert result["fail_count"] == 0
    assert result["p95"] <= 0.7


def test_pairwise_long_report_audit_prepares_each_text_once():
    from core.diversity_audit import audit_section_texts

    texts = {
        f"样例-{case:03d}": "".join(
            f"第{index}段命盘{case}需要核对资源、合同与行动边界。" for index in range(120)
        )
        for case in range(1, 41)
    }
    started = time.perf_counter()
    result = audit_section_texts("长报告", texts)

    assert time.perf_counter() - started < 1.5
    assert result["pair_count"] == 780


def test_monthly_event_overlap_uses_top_three_event_types():
    from core.diversity_audit import audit_monthly_event_overlap

    bundles = [
        {
            "case_id": "样例-001",
            "monthly_events": [
                {"month": month, "top_events": [{"event_type": value} for value in ("a", "b", "c")]}
                for month in range(1, 13)
            ],
        },
        {
            "case_id": "样例-002",
            "monthly_events": [
                {"month": month, "top_events": [{"event_type": value} for value in ("a", "d", "e")]}
                for month in range(1, 13)
            ],
        },
    ]

    result = audit_monthly_event_overlap(bundles)

    assert result["cross_chart_same_month_average"] == 0.2
    assert result["per_chart_max_month_repeat"] == 1.0


def test_full_diversity_audit_exposes_thresholds_and_top_twenty():
    from core.diversity_audit import audit_bundle_diversity, build_case_bundle
    from scripts.build_final_40_case_matrix import load_frozen_matrix

    bundles = [build_case_bundle(case, target_year=2026) for case in load_frozen_matrix()]
    result = audit_bundle_diversity(bundles)

    assert set(result["sections"]) == {"identity", "five_dimensions", "career", "wealth", "relationship", "yearly", "monthly"}
    assert all(section["pair_count"] == 780 for section in result["sections"].values())
    assert len(result["top_similar_pairs"]) == 20
    assert result["thresholds"] == {"fail_above": 0.85, "review_from": 0.7, "p95_max": 0.7}
