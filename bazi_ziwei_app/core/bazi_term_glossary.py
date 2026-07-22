"""首批命理术语词典，以及只基于现有命盘字段的个人化观察。"""

from __future__ import annotations

from copy import deepcopy

from core.bazi_constants import CONTROLLING, EARTHLY_BRANCHES, GENERATING, STEM_ELEMENTS
from core.ten_god_explanations import TEN_GOD_EXPLANATIONS, TEN_GOD_TERM_IDS


BASE_TERM_IDS = (
    "day-master",
    "strength-strong",
    "strength-weak",
    "five-elements",
    "favorable-elements",
    "unfavorable-elements",
    "pattern",
)
GROUP_TERM_IDS = (
    "wealth-star",
    "officer-star",
    "output-star",
    "resource-star",
    "peer-star",
)

_BASE_TERMS: dict[str, dict[str, str]] = {
    "day-master": {
        "label": "日主",
        "definition": "日主是日柱天干，作为观察命盘其他五行与十神关系的参照点。",
        "observation_scope": "观察一个人的基本取向、承压方式，以及其他五行相对日主形成的关系。",
        "boundary": "日主只是命盘的参照核心，不能脱离月令、强弱和全局配置单独定性。",
    },
    "strength-strong": {
        "label": "身强",
        "definition": "身强表示日主在季节、根气和生扶等条件下，相对有较足的承载力量。",
        "observation_scope": "观察日主承接财官、输出与外部压力时是否有较多余量。",
        "boundary": "身强不等于能力更强或人生更好，仍要看力量是否流通及喜忌配合。",
    },
    "strength-weak": {
        "label": "身弱",
        "definition": "身弱表示日主相对承载力有限，更需要生扶、资源或节奏上的支持。",
        "observation_scope": "观察面对消耗、责任与输出时，是否需要借助环境、团队或恢复条件。",
        "boundary": "身弱不等于软弱或运势差，也不应成为评价性格与现实能力的标签。",
    },
    "five-elements": {
        "label": "五行",
        "definition": "五行是木、火、土、金、水五类关系模型，用来描述命盘中的生克与流通。",
        "observation_scope": "观察各元素的数量、位置、季节状态，以及相互生助或制约的关系。",
        "boundary": "五行数量不等于实际能量，缺少某一行也不能直接推断现实缺陷。",
    },
    "favorable-elements": {
        "label": "喜用",
        "definition": "喜用指在当前强弱判断下，更有助于命盘平衡与流通的五行方向。",
        "observation_scope": "观察哪些元素在原局或阶段环境中较能提供支持、疏导或有效制衡。",
        "boundary": "喜用会受全局结构与岁运变化影响，不能直接等同于颜色、职业或投资建议。",
    },
    "unfavorable-elements": {
        "label": "忌神",
        "definition": "忌神指在当前结构中，过多出现时较容易加重失衡或阻滞的五行方向。",
        "observation_scope": "观察哪些元素叠加后可能增加消耗、压力或某类结构偏差。",
        "boundary": "忌神不是绝对有害；有制化、适量出现或岁运环境改变时，作用也会变化。",
    },
    "pattern": {
        "label": "格局",
        "definition": "格局是依据月令、透干与十神配合，对命盘主要结构线索所作的归纳。",
        "observation_scope": "观察命盘力量集中在哪里，以及主要十神之间如何配合或牵制。",
        "boundary": "格局是结构摘要，不是身份等级，也不能取代对强弱、调候和具体落位的分析。",
    },
}

_GROUPS: dict[str, tuple[str, tuple[str, str], str, str, str]] = {
    "wealth-star": (
        "财星",
        ("正财", "偏财"),
        "财星是日主所克的五行所形成的十神组，包括正财与偏财。",
        "观察资源交换、收入与支出、现实经营，以及对成果的承接方式。",
        "财星不等于必然有钱；数量多寡还要结合日主承载力、位置与喜忌。",
    ),
    "officer-star": (
        "官杀",
        ("正官", "七杀"),
        "官杀是克制日主的五行所形成的十神组，包括正官与七杀。",
        "观察规则、责任、职位、竞争与压力如何进入命盘。",
        "官杀不直接等于职位高低或风险事件，必须结合强弱、制化和具体落位。",
    ),
    "output-star": (
        "食伤",
        ("食神", "伤官"),
        "食伤是日主所生的五行所形成的十神组，包括食神与伤官。",
        "观察表达、作品、技能输出、创意与行动释放的方式。",
        "食伤多不等于一定有才华或反叛，仍要看是否得时、得位并形成有效流通。",
    ),
    "resource-star": (
        "印星",
        ("正印", "偏印"),
        "印星是生助日主的五行所形成的十神组，包括正印与偏印。",
        "观察学习、知识、支持系统、恢复与保护资源。",
        "印星不等于学历或贵人保证，过多时也可能表现为承接过重或行动变慢。",
    ),
    "peer-star": (
        "比劫",
        ("比肩", "劫财"),
        "比劫是与日主同五行的十神组，包括比肩与劫财。",
        "观察自主性、同辈关系、竞争协作与资源边界。",
        "比劫不直接等于朋友好坏或破财，需结合位置、强弱与现实互动判断。",
    ),
}

_GROUP_TERMS = {
    term_id: {
        "label": values[0],
        "definition": values[2],
        "observation_scope": values[3],
        "boundary": values[4],
    }
    for term_id, values in _GROUPS.items()
}

_TEN_GOD_TERMS = {
    term_id: {
        "label": ten_god,
        "definition": TEN_GOD_EXPLANATIONS[ten_god]["meaning"],
        "observation_scope": (
            f'观察{TEN_GOD_EXPLANATIONS[ten_god]["personality"]}'
            f'现实场景也可参考：{TEN_GOD_EXPLANATIONS[ten_god]["career"]}'
        ),
        "boundary": "十神是相对日主形成的关系标签，不能只凭一个十神断定性格、职业或事件。",
    }
    for ten_god, term_id in TEN_GOD_TERM_IDS.items()
}

_STRENGTH_ALIAS_TERM = {
    "label": "日主强弱",
    "definition": "日主强弱是对日主在季节、根气、生扶与克泄条件下相对承载力的概括。",
    "observation_scope": "观察日主承接输出、财官与外部压力时的余量，以及需要何种支持。",
    "boundary": "强弱不是能力高低或人格评价；中和、偏强与偏弱都要结合全局流通理解。",
}

BAZI_TERM_GLOSSARY: dict[str, dict[str, str]] = {
    **_BASE_TERMS,
    **_GROUP_TERMS,
    **_TEN_GOD_TERMS,
}

_TERM_ALIASES = {
    "day-element-wood": "five-elements",
    "day-element-fire": "five-elements",
    "day-element-earth": "five-elements",
    "day-element-metal": "five-elements",
    "day-element-water": "five-elements",
    "day-element-unknown": "five-elements",
    "element-wood": "five-elements",
    "element-fire": "five-elements",
    "element-earth": "five-elements",
    "element-metal": "five-elements",
    "element-water": "five-elements",
}
_PILLAR_LABELS = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
_PILLAR_KEYS = tuple(_PILLAR_LABELS)
_TEN_GOD_BY_ID = {term_id: ten_god for ten_god, term_id in TEN_GOD_TERM_IDS.items()}


def _is_valid_chart(chart: object) -> bool:
    if not isinstance(chart, dict) or chart.get("error"):
        return False
    day_master = chart.get("day_master")
    pillars = chart.get("pillars")
    if day_master not in STEM_ELEMENTS or not isinstance(pillars, dict):
        return False
    for pillar_key in _PILLAR_KEYS:
        pillar = pillars.get(pillar_key)
        if not isinstance(pillar, dict):
            return False
        if pillar.get("gan") not in STEM_ELEMENTS or pillar.get("zhi") not in EARTHLY_BRANCHES:
            return False
    if pillars["day"].get("gan") != day_master:
        return False

    strength = chart.get("day_master_strength")
    counts = chart.get("ten_god_counts")
    five_elements = chart.get("five_elements")
    ten_gods = chart.get("ten_gods")
    hidden_stems = chart.get("hidden_stems")
    pattern = chart.get("pattern_analysis")
    if not isinstance(strength, dict) or not str(strength.get("strength") or "").strip():
        return False
    if not isinstance(strength.get("favorable_elements"), list):
        return False
    if not isinstance(strength.get("unfavorable_elements"), list):
        return False
    if not isinstance(counts, dict) or not counts:
        return False
    if not all(isinstance(value, (int, float)) and value >= 0 for value in counts.values()):
        return False
    if not isinstance(five_elements, dict) or not all(
        element in five_elements for element in ("木", "火", "土", "金", "水")
    ):
        return False
    if not isinstance(ten_gods, dict) or not all(
        isinstance(ten_gods.get(pillar_key), dict) for pillar_key in _PILLAR_KEYS
    ):
        return False
    if not isinstance(hidden_stems, dict) or not all(
        isinstance(hidden_stems.get(pillar_key), list) for pillar_key in _PILLAR_KEYS
    ):
        return False
    return isinstance(pattern, dict) and bool(str(pattern.get("pattern") or "").strip())


def _canonical_term_id(term_id: str, chart: dict | None = None) -> str:
    if term_id == "strength":
        strength_info = chart.get("day_master_strength") if _is_valid_chart(chart) else None
        strength = str(strength_info.get("strength", "")) if isinstance(strength_info, dict) else ""
        if any(word in strength for word in ("弱", "衰")):
            return "strength-weak"
        if any(word in strength for word in ("强", "旺")):
            return "strength-strong"
        return "strength"
    return _TERM_ALIASES.get(term_id, term_id)


def _term_members(term_id: str) -> tuple[str, ...]:
    if term_id in _GROUPS:
        return _GROUPS[term_id][1]
    if term_id in _TEN_GOD_BY_ID:
        return (_TEN_GOD_BY_ID[term_id],)
    return ()


def _ten_god_positions(chart: dict, members: tuple[str, ...]) -> list[str]:
    positions: list[str] = []
    ten_gods = chart.get("ten_gods", {}) if isinstance(chart.get("ten_gods"), dict) else {}
    hidden_stems = chart.get("hidden_stems", {}) if isinstance(chart.get("hidden_stems"), dict) else {}
    for pillar in ("year", "month", "day", "hour"):
        label = _PILLAR_LABELS[pillar]
        pillar_gods = ten_gods.get(pillar, {}) if isinstance(ten_gods.get(pillar), dict) else {}
        if pillar_gods.get("gan") in members:
            positions.append(f"{label}天干")
        for item in hidden_stems.get(pillar, []) or []:
            if isinstance(item, dict) and item.get("ten_god") in members:
                positions.append(f"{label}藏干")
    return positions


def _target_element(day_element: str, term_id: str) -> str:
    if not day_element:
        return ""
    if term_id in {"peer-star", TEN_GOD_TERM_IDS["比肩"], TEN_GOD_TERM_IDS["劫财"]}:
        return day_element
    if term_id in {"output-star", TEN_GOD_TERM_IDS["食神"], TEN_GOD_TERM_IDS["伤官"]}:
        return GENERATING.get(day_element, "")
    if term_id in {"wealth-star", TEN_GOD_TERM_IDS["正财"], TEN_GOD_TERM_IDS["偏财"]}:
        return CONTROLLING.get(day_element, "")
    if term_id in {"officer-star", TEN_GOD_TERM_IDS["正官"], TEN_GOD_TERM_IDS["七杀"]}:
        return next((element for element, controlled in CONTROLLING.items() if controlled == day_element), "")
    if term_id in {"resource-star", TEN_GOD_TERM_IDS["正印"], TEN_GOD_TERM_IDS["偏印"]}:
        return next((element for element, generated in GENERATING.items() if generated == day_element), "")
    return ""


def _relation(element: str, strength: dict) -> str:
    if element and element in set(strength.get("favorable_elements", []) or []):
        return "喜用相关"
    if element and element in set(strength.get("unfavorable_elements", []) or []):
        return "忌神相关"
    return "中性观察"


def _ten_god_personalized_view(term_id: str, term: dict[str, str], chart: dict) -> dict:
    strength = chart.get("day_master_strength", {})
    strength = strength if isinstance(strength, dict) else {}
    day_element = STEM_ELEMENTS.get(str(chart.get("day_master", "")), "")
    members = _term_members(term_id)
    positions = _ten_god_positions(chart, members)
    counts = chart.get("ten_god_counts", {}) if isinstance(chart.get("ten_god_counts"), dict) else {}
    count = sum(int(counts.get(member, 0) or 0) for member in members)
    target_element = _target_element(day_element, term_id)
    relation = _relation(target_element, strength)
    role = f"{target_element} · {term['label']}" if target_element else term["label"]
    where = "、".join(positions) if positions else "原局未见明确落位"
    interpretation = (
        f"本盘{term['label']}共{count}处，位置为{where}；当前属于{relation}。"
        "数量只是线索，应连同强弱、位置和现实经历一起理解。"
    )
    return {
        "count": count,
        "positions": positions,
        "element_role": role,
        "favorable_relation": relation,
        "interpretation": interpretation,
    }


def _base_personalized_view(term_id: str, chart: dict) -> dict:
    strength = chart.get("day_master_strength", {})
    strength = strength if isinstance(strength, dict) else {}
    day_master = str(chart.get("day_master") or "")
    day_element = STEM_ELEMENTS.get(day_master, "")
    strength_label = str(strength.get("strength") or "暂无法判断")
    favorable = [str(item) for item in strength.get("favorable_elements", []) or []]
    unfavorable = [str(item) for item in strength.get("unfavorable_elements", []) or []]

    if term_id == "day-master":
        relation = _relation(day_element, strength)
        return {
            "day_master": day_master,
            "day_element": day_element,
            "favorable_relation": relation,
            "interpretation": f"本盘日主为{day_master}{day_element}；当前属于{relation}。",
        }
    if term_id in {"strength", "strength-strong", "strength-weak"}:
        return {
            "current_judgment": strength_label,
            "favorable_elements": favorable,
            "unfavorable_elements": unfavorable,
            "interpretation": (
                f"当前日主强弱判断为{strength_label}。"
                "强弱是承载方式的观察，不代表能力高低或人生好坏。"
            ),
        }
    if term_id == "five-elements":
        distribution = chart.get("five_elements", {})
        distribution = dict(distribution) if isinstance(distribution, dict) else {}
        readable = "、".join(f"{element}{value}" for element, value in distribution.items()) or "暂无分布数据"
        return {
            "distribution": distribution,
            "interpretation": f"本盘五行分布为{readable}；分值用于比较结构，不直接代表吉凶。",
        }
    if term_id in {"favorable-elements", "unfavorable-elements"}:
        related = favorable if term_id == "favorable-elements" else unfavorable
        relation = "喜用相关" if term_id == "favorable-elements" else "忌神相关"
        readable = "、".join(related) or "暂未明确"
        return {
            "related_elements": related,
            "favorable_relation": relation,
            "interpretation": f"当前{relation}元素为{readable}；仍需结合全局和阶段变化理解。",
        }
    pattern = chart.get("pattern_analysis", {})
    pattern = pattern if isinstance(pattern, dict) else {}
    current_pattern = str(pattern.get("pattern") or "暂无法判断")
    return {
        "current_pattern": current_pattern,
        "interpretation": f"当前格局判断为{current_pattern}；格局是结构摘要，不是身份等级。",
    }


def _personalized_view(term_id: str, term: dict[str, str], chart: dict) -> dict:
    if _term_members(term_id):
        return _ten_god_personalized_view(term_id, term, chart)
    return _base_personalized_view(term_id, chart)


def build_term_view(term_id: str, chart: dict | None = None) -> dict:
    """返回可 JSON 序列化的词条；仅在有效命盘存在时加入个人化观察。"""
    canonical_id = _canonical_term_id(str(term_id), chart)
    if canonical_id == "strength":
        term = _STRENGTH_ALIAS_TERM
    elif canonical_id in BAZI_TERM_GLOSSARY:
        term = BAZI_TERM_GLOSSARY[canonical_id]
    else:
        raise KeyError(f"未知命理术语：{term_id}")
    view = {"term_id": canonical_id, **deepcopy(term)}
    if _is_valid_chart(chart):
        view["personalized"] = _personalized_view(canonical_id, view, chart)
    return view


def collect_term_ids(
    seed_term_ids: list[str], texts: list[str], chart: dict | None = None
) -> list[str]:
    """合并展示模型中的 term_id 与文案中可明确识别的正式术语。"""
    result: list[str] = []
    for term_id in seed_term_ids:
        canonical = _canonical_term_id(str(term_id), chart)
        if (canonical in BAZI_TERM_GLOSSARY or canonical == "strength") and canonical not in result:
            result.append(canonical)
    joined = "\n".join(str(text or "") for text in texts)
    matches = sorted(
        (
            (joined.find(term["label"]), order, term_id)
            for order, (term_id, term) in enumerate(BAZI_TERM_GLOSSARY.items())
            if term["label"] in joined
        ),
        key=lambda item: (item[0], item[1]),
    )
    for _position, _order, term_id in matches:
        if term_id not in result:
            result.append(term_id)
    return result
