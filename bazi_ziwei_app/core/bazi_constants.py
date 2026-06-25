"""八字基础常量。"""

HEAVENLY_STEMS: list[str] = list("甲乙丙丁戊己庚辛壬癸")
EARTHLY_BRANCHES: list[str] = list("子丑寅卯辰巳午未申酉戌亥")

STEM_ELEMENTS: dict[str, str] = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

STEM_YIN_YANG: dict[str, str] = {
    "甲": "阳",
    "乙": "阴",
    "丙": "阳",
    "丁": "阴",
    "戊": "阳",
    "己": "阴",
    "庚": "阳",
    "辛": "阴",
    "壬": "阳",
    "癸": "阴",
}

BRANCH_HIDDEN_STEMS: dict[str, list[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

BRANCH_MAIN_ELEMENTS: dict[str, str] = {
    branch: STEM_ELEMENTS[hidden_stems[0]]
    for branch, hidden_stems in BRANCH_HIDDEN_STEMS.items()
}

GENERATING: dict[str, str] = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

CONTROLLING: dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

FIVE_ELEMENT_ORDER: list[str] = ["木", "火", "土", "金", "水"]
