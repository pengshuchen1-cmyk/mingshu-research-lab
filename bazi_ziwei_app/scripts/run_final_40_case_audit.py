"""运行最终 40 命例审计并生成检查点 A 的 JSON/中文报告。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.diversity_audit import (
    audit_bundle_diversity,
    audit_case_usability,
    build_case_bundle,
)
from scripts.build_final_40_case_matrix import (
    DEFAULT_OUTPUT as DEFAULT_MATRIX,
    load_frozen_matrix,
    validate_case_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "acceptance_samples" / "final_40_case_audit.json"
DEFAULT_MARKDOWN = ROOT / "acceptance_samples" / "final_40_case_audit.md"
SECTION_LABELS = {
    "identity": "个人身份卡与术语",
    "five_dimensions": "五维洞察",
    "career": "事业专项",
    "wealth": "财富专项",
    "relationship": "关系专项",
    "yearly": "2026 年度",
    "monthly": "2026 十二流月与重点事件",
}


def build_checkpoint(result: dict[str, Any]) -> dict[str, Any]:
    critical: list[str] = []
    important: list[str] = []
    review: list[str] = []
    coverage = result["coverage"]
    usability = result["usability"]
    diversity = result["diversity"]

    critical.extend(str(item) for item in coverage.get("errors", []))
    if usability.get("failed_count", 0):
        critical.append(f"{usability['failed_count']} 个样例完整链路失败")
    if usability.get("deterministic_count") != coverage.get("case_count"):
        critical.append("存在同一输入重复运行结果不一致")
    if usability.get("json_safe_count") != coverage.get("case_count"):
        critical.append("存在无法稳定 JSON 序列化的交付模型")
    if usability.get("core_p95_seconds", 0) > 0.5:
        important.append(f"核心排盘 P95 为 {usability['core_p95_seconds']:.3f} 秒，超过 0.5 秒")
    if usability.get("full_p95_seconds", 0) > 5.0:
        important.append(f"完整链路 P95 为 {usability['full_p95_seconds']:.3f} 秒，超过 5 秒")

    for key, section in diversity["sections"].items():
        label = SECTION_LABELS.get(key, key)
        if section.get("exact_duplicate_count", 0):
            critical.append(f"{label}出现 {section['exact_duplicate_count']} 对完全相同正文")
        high_failures = section.get("fail_count", 0) - section.get("exact_duplicate_count", 0)
        if high_failures:
            important.append(f"{label}存在 {high_failures} 对相似度高于 0.85 的正文")
        if not section.get("p95_passed", False):
            important.append(f"{label}的 P95={section['p95']:.3f}，高于 0.70")
        if section.get("review_count", 0):
            review.append(f"{label}有 {section['review_count']} 对落在 0.70–0.85，需人工复核")

    overlap = diversity["monthly_event_overlap"]
    if not overlap.get("cross_chart_passed", False):
        important.append(
            f"同月 Top 3 事件跨命盘平均重合度 {overlap['cross_chart_same_month_average']:.3f}，高于 0.35"
        )
    if not overlap.get("per_chart_passed", False):
        important.append(
            f"单命盘月间事件最大重复率 {overlap['per_chart_max_month_repeat']:.3f}，高于 0.50"
        )

    if critical:
        status = "阻断：先修复可用性或完全重复问题"
    elif important:
        status = "需要最小修复清单"
    elif review:
        status = "通过自动闸门，等待人工复核"
    else:
        status = "检查点 A 全部通过"
    return {"status": status, "critical": critical, "important": important, "review": review}


def render_markdown_report(result: dict[str, Any]) -> str:
    coverage = result["coverage"]
    usability = result["usability"]
    diversity = result["diversity"]
    overlap = diversity["monthly_event_overlap"]
    checkpoint = result["checkpoint"]
    lines = [
        "# 命数研究室最终收口：40 命例审计报告（检查点 A）",
        "",
        f"生成时间：{result['generated_at']}",
        "",
        "## 一、结论",
        "",
        f"**当前状态：{checkpoint['status']}**",
        "",
        f"- 完整链路通过：{usability['passed_count']}/{coverage['case_count']}（即 {usability['passed_count']}/40）",
        f"- 四柱唯一：{coverage['unique_pillars']}/40；核心指纹唯一：{coverage['unique_fingerprints']}/40",
        f"- 确定性复算：{usability['deterministic_count']}/40；JSON 序列化：{usability['json_safe_count']}/40",
        f"- 核心排盘 P95：{usability['core_p95_seconds']:.3f} 秒；完整链路 P95：{usability['full_p95_seconds']:.3f} 秒",
        "",
        "## 二、40 例覆盖矩阵",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| 样例数量 | {coverage['case_count']} |",
        f"| 唯一四柱 | {coverage['unique_pillars']} |",
        f"| 唯一核心指纹 | {coverage['unique_fingerprints']} |",
        f"| 节气/子时/真太阳时边界样例 | {coverage['boundary_case_count']} |",
        "",
        "## 三、七个板块的 780 对比较",
        "",
        "阈值：完全相同或相似度大于 0.85 为失败；0.70–0.85 进入人工复核；各板块 P95 不得高于 0.70。",
        "",
        "| 板块 | 比较对数 | 完全相同 | 高相似失败（含完全相同） | 人工复核 | P95 | 最大值 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, section in diversity["sections"].items():
        lines.append(
            f"| {SECTION_LABELS.get(key, key)} | {section['pair_count']} | "
            f"{section['exact_duplicate_count']} | {section['fail_count']} | {section['review_count']} | "
            f"{section['p95']:.3f} | {section['max_score']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 四、月度重点事件",
            "",
            f"- 同月 Top 3 事件跨命盘平均重合度：{overlap['cross_chart_same_month_average']:.3f}（要求 ≤ 0.35）",
            f"- 单命盘月间事件最大重复率：{overlap['per_chart_max_month_repeat']:.3f}（要求 ≤ 0.50）",
            "",
            "## 五、最相似 20 对",
            "",
            "| 排名 | 板块 | 左侧 | 右侧 | 综合相似度 | SequenceMatcher | 3-gram Dice | 分级 |",
            "|---:|---|---|---|---:|---:|---:|---|",
        ]
    )
    for index, pair in enumerate(diversity["top_similar_pairs"], start=1):
        lines.append(
            f"| {index} | {SECTION_LABELS.get(pair['section'], pair['section'])} | {pair['left']} | "
            f"{pair['right']} | {pair['score']:.3f} | {pair['sequence']:.3f} | "
            f"{pair['char_3gram_dice']:.3f} | {pair['classification']} |"
        )
    lines.extend(["", "## 六、问题分级与下一步", ""])
    for label, key in (("Critical", "critical"), ("Important", "important"), ("人工复核", "review")):
        lines.append(f"### {label}")
        lines.append("")
        items = checkpoint[key]
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 无")
        lines.append("")
    lines.extend(
        [
            "本检查点只报告问题，不自动改写核心算法。若需修复，将针对具体样例与板块先补 RED 测试，再做最小修改并保留前后对比。",
            "",
        ]
    )
    return "\n".join(lines)


def run_audit(matrix_path: Path = DEFAULT_MATRIX) -> dict[str, Any]:
    cases = load_frozen_matrix(matrix_path)
    coverage = validate_case_matrix(cases, recalculate=True)
    usability = audit_case_usability(cases, target_year=2026, verify_determinism=True)
    bundles = [build_case_bundle(case, target_year=2026) for case in cases]
    diversity = audit_bundle_diversity(bundles)
    result = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_year": 2026,
        "coverage": coverage,
        "usability": usability,
        "diversity": diversity,
    }
    result["checkpoint"] = build_checkpoint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    result = run_audit(args.matrix)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown_report(result), encoding="utf-8")
    print(json.dumps({"checkpoint": result["checkpoint"], "outputs": [str(args.json_output), str(args.markdown_output)]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
