"""Generate a bazi-skill algorithm comparison report.

The report is intentionally conservative: it records what the current project
already supports, what still needs human review, and which tests guard the
boundary cases.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "reports" / "bazi_skill_algorithm_review.md"


def _has_text(path: str, *needles: str) -> bool:
    text = (ROOT / path).read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def build_bazi_skill_review_report(write_file: bool = True) -> str:
    """Build a Markdown review against the installed bazi-skill rules."""
    checks = [
        {
            "item": "立春换年",
            "status": "已接入，仍建议持续用边界样例复核",
            "basis": "四柱来自 lunar_python 的 EightChar，测试中已有立春前后年柱断言。",
            "files": "core/calendar_engine.py；tests/test_bazi_algorithm_accuracy.py；tests/test_jieqi_boundary_month_pillar.py",
            "risk": "依赖 lunar_python 版本行为，若库接口变化，需要重新跑边界测试。",
        },
        {
            "item": "节气定月",
            "status": "已接入",
            "basis": "月柱由 lunar_python 按节气体系生成，项目已有节气边界 fixture。",
            "files": "core/calendar_engine.py；tests/fixtures/jieqi_boundary_cases.json",
            "risk": "节气交界小时仍需要以已知万年历样例持续校验。",
        },
        {
            "item": "早晚子时",
            "status": "已增加用户可见提示，不改变既有排盘",
            "basis": "23:00-00:59 出生会提示早晚子时和换日流派差异，建议作为复核点。",
            "files": "core/calendar_engine.py；core/bazi_engine.py；ui/profile_form.py",
            "risk": "当前只提示，不自动生成两套子时盘，避免破坏已有排盘结果。",
        },
        {
            "item": "起运顺逆与起运年龄",
            "status": "已由 lunar_python 处理，并有负数年龄保护",
            "basis": "大运通过 EightChar.getYun(gender_code) 获取，年龄区间经 _normalize_age_range 保护。",
            "files": "core/luck_engine.py；tests/test_algorithm_boundaries.py",
            "risk": "顺逆规则由依赖库承担，后续建议增加阳男阴女顺、阴男阳女逆的显式说明。",
        },
        {
            "item": "真太阳时",
            "status": "已接入，用户勾选后按经度校正",
            "basis": "使用东经 120 度为北京时间基准，每 1 度约 4 分钟校正。",
            "files": "core/calendar_engine.py；core/bazi_engine.py；ui/profile_form.py；tests/test_true_solar_time_integration.py",
            "risk": "当前为经度时差校正，未加入均时差；页面已提示可能影响时柱。",
        },
        {
            "item": "调候解释",
            "status": "已增加解释层，不改变强弱评分",
            "basis": "结合月令季节给出寒暖燥湿的白话解释，参考《穷通宝鉴》调候思路。",
            "files": "core/strength_engine.py",
            "risk": "当前是解释层，不直接参与用神评分，后续可由真实反馈校准。",
        },
    ]

    lines = [
        "# bazi-skill 算法复核报告",
        "",
        "本报告对照已安装的 bazi-skill，检查命数研究室当前八字算法边界。结论只用于工程复核，不作为绝对命理判断。",
        "",
        "## 总结",
        "- 当前项目已具备立春换年、节气定月、真太阳时、大运、纳音、旬空、十二长生等基础能力。",
        "- 本轮新增早晚子时用户可见提示，以及调候解释层。",
        "- 起运顺逆目前主要依赖 lunar_python，建议后续把顺逆依据显示到页面和报告中。",
        "",
        "## 对照清单",
    ]
    for check in checks:
        lines.extend(
            [
                f"### {check['item']}",
                f"- 状态：{check['status']}",
                f"- 依据：{check['basis']}",
                f"- 涉及文件：{check['files']}",
                f"- 风险/边界：{check['risk']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 建议下一步",
            "1. 增加页面上的起运顺逆解释：阳男阴女顺，阴男阳女逆。",
            "2. 为 23:00-00:59 增加可选的双盘复核，但不要默认改变当前排盘。",
            "3. 用匿名边界样例做算法回归验收，不用于规则权重或运行时注入。",
            "",
        ]
    )
    output = "\n".join(lines)
    if write_file:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(output + "\n", encoding="utf-8")
    return output


def run() -> Path:
    build_bazi_skill_review_report(write_file=True)
    return REPORT_PATH


if __name__ == "__main__":
    path = run()
    print(f"已生成：{path}")
