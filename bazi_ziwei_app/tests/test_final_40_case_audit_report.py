"""最终 40 命例审计报告的稳定交付格式。"""

from __future__ import annotations


def test_markdown_report_contains_checkpoint_a_decision_information():
    from scripts.run_final_40_case_audit import render_markdown_report

    report = render_markdown_report(
        {
            "generated_at": "2026-07-17T12:00:00+08:00",
            "coverage": {"case_count": 40, "unique_pillars": 40, "unique_fingerprints": 40, "boundary_case_count": 8, "errors": []},
            "usability": {"passed_count": 40, "failed_count": 0, "deterministic_count": 40, "json_safe_count": 40, "core_p95_seconds": 0.1, "full_p95_seconds": 2.0},
            "diversity": {
                "thresholds": {"fail_above": 0.85, "review_from": 0.7, "p95_max": 0.7},
                "sections": {
                    "career": {"pair_count": 780, "exact_duplicate_count": 0, "fail_count": 1, "review_count": 2, "p95": 0.65, "max_score": 0.9, "p95_passed": True}
                },
                "top_similar_pairs": [{"section": "career", "left": "样例-001", "right": "样例-002", "score": 0.9, "sequence": 0.8, "char_3gram_dice": 0.9, "classification": "失败：相似度过高"}],
                "monthly_event_overlap": {"cross_chart_same_month_average": 0.2, "per_chart_max_month_repeat": 0.4, "cross_chart_passed": True, "per_chart_passed": True},
            },
            "checkpoint": {"status": "需要最小修复清单", "critical": [], "important": ["事业板块存在 1 对高相似正文"], "review": ["事业板块有 2 对需人工复核"]},
        }
    )

    for text in ("检查点 A", "40/40", "最相似 20 对", "事业", "样例-001", "需要最小修复清单"):
        assert text in report
