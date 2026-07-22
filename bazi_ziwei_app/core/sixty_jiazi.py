"""六十甲子与纳音知识层。

本模块只负责知识查询、普通用户解释和边界提示，不参与断事评分。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS


ROOT = Path(__file__).resolve().parents[1]
JIAZI_RULE_PATH = ROOT / "rules" / "sixty_jiazi.json"
BASE_YEAR = 1984

NAYIN_PLAIN_HINTS = {
    "金": "纳音带金，多用于说明这一组干支在传统体系里的象意偏向，常借金属、规则、收束来作比喻。",
    "木": "纳音带木，多用于说明这一组干支在传统体系里的象意偏向，常借生长、规划、延展来作比喻。",
    "水": "纳音带水，多用于说明这一组干支在传统体系里的象意偏向，常借流动、信息、沟通来作比喻。",
    "火": "纳音带火，多用于说明这一组干支在传统体系里的象意偏向，常借表达、热度、行动来作比喻。",
    "土": "纳音带土，多用于说明这一组干支在传统体系里的象意偏向，常借承载、稳定、积累来作比喻。",
}

ELEMENT_REALITY_MAP = {
    "木": {
        "keywords": ["成长", "规划", "学习", "生发"],
        "reality": "现实里常映射为学习成长、规划扩展、审美创意、人际生发。",
        "advice": "建议把想法写成计划，循序推进，避免只想扩张而忽略落地。",
    },
    "火": {
        "keywords": ["表达", "行动", "曝光", "热度"],
        "reality": "现实里常映射为表达展示、行动推进、传播曝光、情绪热度。",
        "advice": "建议主动表达和推进事项，同时留意节奏，避免过急过耗。",
    },
    "土": {
        "keywords": ["稳定", "承载", "资源", "积累"],
        "reality": "现实里常映射为稳定积累、组织承载、土地房产、现实责任。",
        "advice": "建议建立秩序和长期积累，也要避免过度保守或压力堆积。",
    },
    "金": {
        "keywords": ["规则", "结构", "执行", "收束"],
        "reality": "现实里常映射为规则制度、技术结构、执行标准、边界收束。",
        "advice": "建议做清晰规范和专业精修，也要注意表达不要过硬。",
    },
    "水": {
        "keywords": ["流动", "信息", "沟通", "调度"],
        "reality": "现实里常映射为信息流动、沟通咨询、资源调度、出行变化。",
        "advice": "建议保持弹性和信息敏感度，也要避免想太多、落地太慢。",
    },
}

STEM_PLAIN_HINTS = {
    "甲": "甲木像树木，重视方向、原则和向上生长。",
    "乙": "乙木像花草藤蔓，重视弹性、审美和关系协调。",
    "丙": "丙火像太阳，重视表达、热度和外在影响力。",
    "丁": "丁火像灯火，重视细腻、灵感和持续照亮。",
    "戊": "戊土像山岳，重视承载、稳定和现实框架。",
    "己": "己土像田园，重视照顾、积累和细致经营。",
    "庚": "庚金像矿铁，重视执行、决断和结构打磨。",
    "辛": "辛金像珠玉，重视品质、精修和审美边界。",
    "壬": "壬水像江河，重视流动、视野和资源调度。",
    "癸": "癸水像雨露，重视感受、信息和细微变化。",
}

BRANCH_PLAIN_HINTS = {
    "子": "子水偏向信息、流动、思考和夜间节奏。",
    "丑": "丑土偏向积累、仓储、耐心和现实事务。",
    "寅": "寅木偏向启动、开拓、学习和新机会。",
    "卯": "卯木偏向审美、人缘、协调和成长空间。",
    "辰": "辰土偏向承载、变化、资源整合和湿土蓄水。",
    "巳": "巳火偏向表达、技术、热度和隐含转化。",
    "午": "午火偏向行动、曝光、推进和外在表现。",
    "未": "未土偏向整理、家庭、承接和阶段收尾。",
    "申": "申金偏向规则、效率、交通移动和技术执行。",
    "酉": "酉金偏向审美、标准、精修和人际边界。",
    "戌": "戌土偏向责任、守成、制度和压力承载。",
    "亥": "亥水偏向远方、灵感、流动和潜在资源。",
}


@lru_cache(maxsize=1)
def load_sixty_jiazi() -> list[dict]:
    """加载六十甲子知识库。"""
    with JIAZI_RULE_PATH.open("r", encoding="utf-8") as fp:
        rows = json.load(fp)
    return [_enrich_entry(row) for row in rows]


def _nayin_element(nayin: str) -> str:
    """从纳音名称提取五行。"""
    for element in ["木", "火", "土", "金", "水"]:
        if nayin.endswith(element):
            return element
    return ""


def _sample_years(index: int, *, start: int = 1924, end: int = 2043) -> list[int]:
    """给一个干支生成用户容易理解的年份示例。"""
    target_offset = index - 1
    years = []
    for year in range(start, end + 1):
        if (year - BASE_YEAR) % 60 == target_offset:
            years.append(year)
    return years


def _enrich_entry(row: dict) -> dict:
    pillar = row["pillar"]
    gan, zhi = pillar[0], pillar[1]
    nayin = row["nayin"]
    nayin_element = _nayin_element(nayin)
    reality_hint = ELEMENT_REALITY_MAP.get(nayin_element, {})
    symbolic_keywords = list(dict.fromkeys(
        [*reality_hint.get("keywords", []), STEM_ELEMENTS.get(gan, ""), BRANCH_MAIN_ELEMENTS.get(zhi, "")]
    ))
    entry = {
        **row,
        "gan": gan,
        "zhi": zhi,
        "gan_element": STEM_ELEMENTS.get(gan, ""),
        "zhi_element": BRANCH_MAIN_ELEMENTS.get(zhi, ""),
        "nayin_element": nayin_element,
        "sample_years": _sample_years(int(row["index"])),
        "plain_explanation": (
            f"{pillar}由天干“{gan}”和地支“{zhi}”组成，天干属{STEM_ELEMENTS.get(gan, '未知')}，"
            f"地支主气属{BRANCH_MAIN_ELEMENTS.get(zhi, '未知')}。纳音为“{nayin}”，"
            f"{NAYIN_PLAIN_HINTS.get(nayin_element, '可作为传统文化象意的辅助说明。')}"
        ),
        "symbolic_keywords": symbolic_keywords,
        "reality_mapping": (
            f"现实映射：{STEM_PLAIN_HINTS.get(gan, '')}"
            f"{BRANCH_PLAIN_HINTS.get(zhi, '')}"
            f"纳音“{nayin}”可辅助理解为：{reality_hint.get('reality', '传统文化象意。')}"
        ),
        "user_advice": (
            f"{reality_hint.get('advice', '建议结合完整命盘和现实处境综合理解。')}"
        ),
        "lichun_boundary_note": (
            "八字年柱通常以立春为换年点，不是简单按公历1月1日切换；"
            "如果生日在2月3日至2月5日前后，需要结合当年立春时间复核。"
        ),
    }
    return entry


def get_jiazi_by_year(year: int) -> dict:
    """按公历年份给出六十甲子速查结果，并附带立春边界提醒。"""
    rows = load_sixty_jiazi()
    index = (int(year) - BASE_YEAR) % 60
    return rows[index]


def get_jiazi_by_pillar(pillar: str) -> dict | None:
    """按干支名称查询六十甲子。"""
    for row in load_sixty_jiazi():
        if row["pillar"] == pillar:
            return row
    return None
