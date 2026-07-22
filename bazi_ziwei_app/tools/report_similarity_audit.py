"""v1.0.4 report similarity audit.

Generate a Markdown audit for five different charts:
- life overview similarity
- score spread
- 2026 monthly Top 3 event overlap
- fallback/generic phrase ratio
"""

from __future__ import annotations

import itertools
import statistics
import sys
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SAMPLE_PROFILES = [
    {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False},
    {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州", "use_solar_time": False},
    {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都", "use_solar_time": False},
    {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
]


GENERIC_PHRASES = [
    "平稳观察",
    "稳步观察",
    "现实反馈",
    "以稳为主",
    "注意沟通",
    "注意作息",
    "持续能力积累",
    "暂无特别突出",
]


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _pairwise(values: list[str]) -> list[float]:
    return [
        _similarity(values[i], values[j])
        for i, j in itertools.combinations(range(len(values)), 2)
    ]


def _event_overlap(left: list[str], right: list[str]) -> float:
    a = set(left)
    b = set(right)
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def _extract_overview_text(item: dict) -> str:
    return "\n".join([
        item.get("overall_pattern", ""),
        item.get("overall_summary", ""),
        item.get("wealth_overview", {}).get("wealth_type", ""),
        item.get("wealth_overview", {}).get("wealth_summary", ""),
        item.get("romance_overview", {}).get("romance_type", ""),
        item.get("romance_overview", {}).get("romance_summary", ""),
        item.get("health_overview", {}).get("health_type", ""),
        item.get("health_overview", {}).get("health_summary", ""),
        item.get("career_overview", {}).get("career_type", ""),
        item.get("career_overview", {}).get("career_summary", ""),
    ])


def _fallback_ratio(text: str) -> float:
    if not text:
        return 0.0
    hits = sum(text.count(p) for p in GENERIC_PHRASES)
    sentences = max(1, len([s for s in text.replace("。", "\n").splitlines() if s.strip()]))
    return hits / sentences


def _score_spread(score_rows: list[dict]) -> dict:
    keys = ["wealth", "romance", "health_stability", "career", "overall_balance"]
    result = {}
    for key in keys:
        vals = [float(row.get(key, 0)) for row in score_rows]
        result[key] = {
            "min": min(vals),
            "max": max(vals),
            "spread": max(vals) - min(vals),
            "stdev": round(statistics.pstdev(vals), 2),
        }
    return result


def run_audit() -> str:
    from core.bazi_engine import build_bazi_chart
    from core.life_overview_engine import analyze_life_overview
    from core.monthly_engine import analyze_monthly_fortune
    from core.monthly_event_activation_bridge import infer_monthly_likely_events_full
    from core.yearly_engine import analyze_yearly_fortune

    charts = [build_bazi_chart(profile) for profile in SAMPLE_PROFILES]
    overviews = [analyze_life_overview(chart) for chart in charts]
    overview_texts = [_extract_overview_text(item) for item in overviews]
    overview_sims = _pairwise(overview_texts)
    score_rows = [item.get("scores", {}) for item in overviews]
    spreads = _score_spread(score_rows)

    all_month_top3: list[list[list[str]]] = []
    for chart in charts:
        yearly = analyze_yearly_fortune(chart, 2026)
        monthly = analyze_monthly_fortune(chart, 2026)
        rows = []
        for item in monthly:
            result = infer_monthly_likely_events_full(chart, item, yearly)
            rows.append([e.get("event_type", "") for e in result.get("top_events", [])[:3]])
        all_month_top3.append(rows)

    same_month_overlaps = []
    for month_idx in range(12):
        for i, j in itertools.combinations(range(len(charts)), 2):
            same_month_overlaps.append(_event_overlap(all_month_top3[i][month_idx], all_month_top3[j][month_idx]))

    internal_repeat_rates = []
    for rows in all_month_top3:
        flat = [event for month in rows for event in month]
        internal_repeat_rates.append(1 - (len(set(flat)) / max(1, len(flat))))

    fallback_ratios = [_fallback_ratio(text) for text in overview_texts]

    lines = [
        "# v1.0.4 报告相似度审计",
        "",
        "本报告用于检查 5 个不同命盘在命局总论、评分和 2026 流月事件上的差异度。",
        "",
        "## 样例命盘",
    ]
    for profile, chart in zip(SAMPLE_PROFILES, charts):
        pillars = chart.get("pillars", {})
        lines.append(
            f"- {profile['name']}：{profile['gender']}，{profile['birth_date']} {profile['birth_hour']}点，"
            f"{pillars.get('year', {}).get('pillar', '')} "
            f"{pillars.get('month', {}).get('pillar', '')} "
            f"{pillars.get('day', {}).get('pillar', '')} "
            f"{pillars.get('hour', {}).get('pillar', '')}"
        )

    lines.extend([
        "",
        "## 命局总论文本相似度",
        f"- 最大相似度：{max(overview_sims) if overview_sims else 0:.3f}",
        f"- 平均相似度：{statistics.mean(overview_sims) if overview_sims else 0:.3f}",
        "",
        "## 命盘总览评分差异",
    ])
    for key, item in spreads.items():
        lines.append(f"- {key}：最低 {item['min']:.0f}，最高 {item['max']:.0f}，差距 {item['spread']:.0f}，标准差 {item['stdev']}")

    lines.extend([
        "",
        "## 2026 同年同月 Top 3 事件重合度",
        f"- 平均重合度：{statistics.mean(same_month_overlaps) if same_month_overlaps else 0:.3f}",
        f"- 最高重合度：{max(same_month_overlaps) if same_month_overlaps else 0:.3f}",
        "",
        "## 同一命盘 12 个月事件重复率",
    ])
    for profile, rate in zip(SAMPLE_PROFILES, internal_repeat_rates):
        lines.append(f"- {profile['name']}：{rate:.3f}")

    lines.extend([
        "",
        "## 默认兜底文案占比",
    ])
    for profile, ratio in zip(SAMPLE_PROFILES, fallback_ratios):
        lines.append(f"- {profile['name']}：{ratio:.3f}")

    lines.extend([
        "",
        "## 2026 流月 Top 3 事件明细",
    ])
    for profile, rows in zip(SAMPLE_PROFILES, all_month_top3):
        lines.append(f"### {profile['name']}")
        for month, events in enumerate(rows, start=1):
            lines.append(f"- {month}月：{'、'.join(events)}")

    output = "\n".join(lines) + "\n"
    report_dir = ROOT / "docs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report_similarity_audit_v1.0.4.md").write_text(output, encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_audit())
