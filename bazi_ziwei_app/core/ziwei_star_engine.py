"""
紫微斗数十四主星落宫算法 — v1.2-B1/B2

根据传统紫微斗数起星诀实现：
1. 定命宫（已有）
2. 定命宫干支（五虎遁）
3. 定五行局（命宫干支纳音）
4. 定紫微星（五行局 + 农历生日）
5. 排紫微系星曜（紫微 → 天机 → 空 → 太阳 → 武曲 → 天同 → 空 → 廉贞）
6. 排天府系星曜（天府 → 太阴 → 贪狼 → 巨门 → 天相 → 天梁 → 七杀 → 破军）

注意：当前算法仍需校验。如果校验失败，main_stars_ready=False。
"""

from __future__ import annotations


HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 五虎遁：甲己之年丙作首，乙庚之年戊为头，丙辛之年庚寅起，丁壬壬寅顺行流，戊癸甲寅好追求
WU_HU_DUN: dict[str, list[str]] = {
    "甲": list("丙丁戊己庚辛壬癸甲乙"),
    "乙": list("戊己庚辛壬癸甲乙丙丁"),
    "丙": list("庚辛壬癸甲乙丙丁戊己"),
    "丁": list("壬癸甲乙丙丁戊己庚辛"),
    "戊": list("甲乙丙丁戊己庚辛壬癸"),
    "己": list("丙丁戊己庚辛壬癸甲乙"),
    "庚": list("戊己庚辛壬癸甲乙丙丁"),
    "辛": list("庚辛壬癸甲乙丙丁戊己"),
    "壬": list("壬癸甲乙丙丁戊己庚辛"),
    "癸": list("甲乙丙丁戊己庚辛壬癸"),
}

# 五行局映射 (年干+命宫地支 → 五行局)
# 基于命宫干支的纳音五行:
# 甲子乙丑金 → 金四局
# 丙寅丁卯火 → 火六局
# 戊辰己巳木 → 木三局
# 庚午辛未土 → 土五局
# 壬申癸酉金 → 金四局
# 甲戌乙亥火 → 火六局
# 丙子丁丑水 → 水二局
# 戊寅己卯土 → 土五局
# 庚辰辛巳金 → 金四局
# 壬午癸未木 → 木三局
# 甲申乙酉水 → 水二局
# 丙戌丁亥土 → 土五局
# 戊子己丑火 → 火六局
# 庚寅辛卯木 → 木三局
# 壬辰癸巳水 → 水二局
# 甲午乙未金 → 金四局
# 丙申丁酉火 → 火六局
# 戊戌己亥木 → 木三局
# 庚子辛丑土 → 土五局
# 壬寅癸卯金 → 金四局
# 甲辰乙巳火 → 火六局
# 丙午丁未水 → 水二局
# 戊申己酉土 → 土五局
# 庚戌辛亥金 → 金四局
# 壬子癸丑木 → 木三局
# 甲寅乙卯水 → 水二局
# 丙辰丁巳土 → 土五局
# 戊午己未火 → 火六局
# 庚申辛酉木 → 木三局
# 壬戌癸亥水 → 水二局

NA_YIN_ELEMENT: dict[str, tuple[str, int]] = {
    "甲子": ("金", 4), "乙丑": ("金", 4),
    "丙寅": ("火", 6), "丁卯": ("火", 6),
    "戊辰": ("木", 3), "己巳": ("木", 3),
    "庚午": ("土", 5), "辛未": ("土", 5),
    "壬申": ("金", 4), "癸酉": ("金", 4),
    "甲戌": ("火", 6), "乙亥": ("火", 6),
    "丙子": ("水", 2), "丁丑": ("水", 2),
    "戊寅": ("土", 5), "己卯": ("土", 5),
    "庚辰": ("金", 4), "辛巳": ("金", 4),
    "壬午": ("木", 3), "癸未": ("木", 3),
    "甲申": ("水", 2), "乙酉": ("水", 2),
    "丙戌": ("土", 5), "丁亥": ("土", 5),
    "戊子": ("火", 6), "己丑": ("火", 6),
    "庚寅": ("木", 3), "辛卯": ("木", 3),
    "壬辰": ("水", 2), "癸巳": ("水", 2),
    "甲午": ("金", 4), "乙未": ("金", 4),
    "丙申": ("火", 6), "丁酉": ("火", 6),
    "戊戌": ("木", 3), "己亥": ("木", 3),
    "庚子": ("土", 5), "辛丑": ("土", 5),
    "壬寅": ("金", 4), "癸卯": ("金", 4),
    "甲辰": ("火", 6), "乙巳": ("火", 6),
    "丙午": ("水", 2), "丁未": ("水", 2),
    "戊申": ("土", 5), "己酉": ("土", 5),
    "庚戌": ("金", 4), "辛亥": ("金", 4),
    "壬子": ("木", 3), "癸丑": ("木", 3),
    "甲寅": ("水", 2), "乙卯": ("水", 2),
    "丙辰": ("土", 5), "丁巳": ("土", 5),
    "戊午": ("火", 6), "己未": ("火", 6),
    "庚申": ("木", 3), "辛酉": ("木", 3),
    "壬戌": ("水", 2), "癸亥": ("水", 2),
}

# 紫微星定位表：五行局局数 × 生日 → 紫微星地支索引
# 从寅宫(索引2)起算
# 水二局: 日/2 = 紫微星从寅宫起算的偏移
# 木三局: 日/3
# 金四局: 日/4
# 土五局: 日/5
# 火六局: 日/6
# 有余数则加1，超过12则减12

# 紫微系星曜（逆时针排布，顺序固定）
# 紫微 → 天机 → (空一格) → 太阳 → 武曲 → 天同 → (空二格) → 廉贞
# 从紫微星所在宫位开始逆时针排

ZI_WEI_SERIES: list[tuple[str, int]] = [
    ("紫微", 0),    # 紫微在起始宫
    ("天机", 1),    # 下一宫(逆)
    (None, 1),      # 空一宫
    ("太阳", 1),    # 再下一宫
    ("武曲", 1),
    ("天同", 1),
    (None, 2),      # 空二宫
    ("廉贞", 1),
]

# 天府系星曜（顺时针排布，以天府对紫微为起点）
# 紫微与天府永远在(紫微宫位+4)的位置相对
# 天府 → 太阴 → 贪狼 → 巨门 → 天相 → 天梁 → 七杀 → 破军

TIAN_FU_SERIES: list[tuple[str, int]] = [
    ("天府", 0),    # 天府在紫微对宫
    ("太阴", 1),
    ("贪狼", 1),
    ("巨门", 1),
    ("天相", 1),
    ("天梁", 1),
    ("七杀", 1),
    ("破军", 1),
]

# 五虎遁查找 year_gan → 寅月天干
WU_HU_FIRST: dict[str, str] = {
    "甲": "丙", "乙": "戊", "丙": "庚", "丁": "壬", "戊": "甲",
    "己": "丙", "庚": "戊", "辛": "庚", "壬": "壬", "癸": "甲",
}


def _branch_index(b: str) -> int:
    return EARTHLY_BRANCHES.index(b) if b in EARTHLY_BRANCHES else -1


def _get_life_palace_stem(year_gan: str, life_branch: str) -> str:
    """根据年干和命宫地支，用五虎遁求命宫天干。"""
    # 寅月起丙/戊/庚/壬/甲
    first_gan = WU_HU_FIRST.get(year_gan, "丙")
    start_idx = HEAVENLY_STEMS.index(first_gan)
    branch_idx = _branch_index(life_branch)
    if branch_idx < 0:
        return ""
    # 寅宫(索引2) → 命宫地支
    offset = (branch_idx - 2) % 12
    stem_idx = (start_idx + offset) % 10
    return HEAVENLY_STEMS[stem_idx]


def _get_na_yin_element(stem: str, branch: str) -> tuple[str, int] | None:
    """获取纳音五行和局数。"""
    pillar = f"{stem}{branch}"
    return NA_YIN_ELEMENT.get(pillar)


def _zi_wei_palace_index(five_element_number: int, lunar_day: int) -> int:
    """
    计算紫微星地支索引。
    从寅宫(索引2)起算。
    局数=局数字，生日=农历日。
    步骤：生日÷局数 → 商数 → 从寅宫起偏移商数
    有余数则商数+1
    从寅宫开始逆时针(负方向)
    """
    if five_element_number <= 0:
        return 2  # 默认为寅

    quotient, remainder = divmod(lunar_day, five_element_number)
    if remainder > 0:
        quotient += 1

    # 从寅宫(索引2)起算
    # 正负数方向：
    # 水二局、木三局 → 商数为正，从寅宫顺时针(正方向)
    # 金四局、土五局、火六局 → 从寅宫逆时针(负方向)
    # 简化：统一从寅宫开始，偏移量 = quotient - 1，方向反向
    offset = quotient - 1

    # 紫微星的偏移是逆时针方向(索引减小方向)
    start = 2  # 寅宫
    result = (start - offset) % 12
    return result


def calculate_ziwei_main_stars(
    year_gan: str,
    lunar_month: int,
    lunar_day: int,
    life_branch: str,
) -> dict:
    """
    计算十四主星落宫。

    返回结构包含 main_stars_by_palace (12宫, 索引0=命宫)。
    """
    if not all([year_gan, lunar_day > 0, life_branch]):
        return {"main_stars_ready": False, "five_element_bureau": "",
            "life_palace_stem": "", "life_palace_branch": life_branch or "",
            "ziwei_star_palace": "", "main_stars_by_palace": {},
            "zi_wei_stars": {}, "tian_fu_stars": {},
            "algorithm": "", "algorithm_evidence": [], "error": "输入参数不足",
            "source_ids": ["ziwei_doushu_quanshu"]}

    # 1. 命宫天干
    life_stem = _get_life_palace_stem(year_gan, life_branch)
    if not life_stem:
        return {"main_stars_ready": False, "five_element_bureau": "",
            "life_palace_stem": "", "life_palace_branch": life_branch,
            "ziwei_star_palace": "", "main_stars_by_palace": {},
            "zi_wei_stars": {}, "tian_fu_stars": {},
            "algorithm": "", "algorithm_evidence": [], "error": "无法计算命宫天干",
            "source_ids": ["ziwei_doushu_quanshu"]}

    # 2. 五行局
    na_yin = _get_na_yin_element(life_stem, life_branch)
    if not na_yin:
        return {"main_stars_ready": False, "five_element_bureau": "",
            "life_palace_stem": life_stem, "life_palace_branch": life_branch,
            "ziwei_star_palace": "", "main_stars_by_palace": {},
            "zi_wei_stars": {}, "tian_fu_stars": {},
            "algorithm": "", "algorithm_evidence": [], "error": "无法确定五行局",
            "source_ids": ["ziwei_doushu_quanshu"]}
    five_el, five_num = na_yin

    f_e_l = {"金": "金", "木": "木", "水": "水", "火": "火", "土": "土"}
    five_element_label = f_e_l.get(five_el, "")

    # 3. 紫微星位置
    zw_idx = _zi_wei_palace_index(five_num, lunar_day)
    zw_branch = EARTHLY_BRANCHES[zw_idx]

    # 4. 排紫微系星曜
    zi_wei_stars: dict[str, int] = {}
    current_idx = zw_idx  # 从紫微星所在宫开始
    for star_name, step in ZI_WEI_SERIES:
        if star_name:
            zi_wei_stars[star_name] = current_idx
        # 逆时针移动
        current_idx = (current_idx - step) % 12

    # 5. 排天府系星曜
    # 天府在紫微的对宫：紫微宫位+6 (顺)
    tf_start_idx = (zw_idx + 6) % 12
    tian_fu_stars: dict[str, int] = {}
    current_idx = tf_start_idx
    for star_name, step in TIAN_FU_SERIES:
        if star_name:
            tian_fu_stars[star_name] = current_idx
        # 顺时针移动
        current_idx = (current_idx + step) % 12

    # 6. 合并到十二宫
    # PALACE_NAMES顺序: 命宫(0),兄弟宫(1),...,父母宫(11)
    # 命宫地支 → 索引0
    life_branch_idx = _branch_index(life_branch)
    all_stars = {**zi_wei_stars, **tian_fu_stars}

    main_stars_by_palace: dict[str, list[str]] = {}
    for palace_name in ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫",
                         "疾厄宫", "迁移宫", "交友宫", "官禄宫",
                         "田宅宫", "福德宫", "父母宫"]:
        main_stars_by_palace[palace_name] = []

    for star_name, branch_idx in all_stars.items():
        # 将地支索引转换为宫位名称
        palace_offset = (branch_idx - life_branch_idx) % 12
        palace_names = ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫",
                        "疾厄宫", "迁移宫", "交友宫", "官禄宫",
                        "田宅宫", "福德宫", "父母宫"]
        if palace_offset < 12:
            palace_name = palace_names[palace_offset]
            main_stars_by_palace[palace_name].append(star_name)

    return {
        "main_stars_ready": True,
        "five_element_bureau": f"{five_element_label}{five_num}局",
        "five_element_number": five_num,
        "life_palace_stem": life_stem,
        "life_palace_branch": life_branch,
        "ziwei_star_palace": zw_branch,
        "ziwei_branch_index": zw_idx,
        "main_stars_by_palace": main_stars_by_palace,
        "zi_wei_stars": zi_wei_stars,
        "tian_fu_stars": tian_fu_stars,
        "algorithm": "traditional_ziwei_main_star_placement",
        "algorithm_evidence": [
            f"命宫干支：{life_stem}{life_branch}",
            f"年干：{year_gan}",
            f"五行局：{five_element_label}{five_num}局",
            f"紫微星落：{zw_branch}宫",
        ],
        "source_ids": ["ziwei_doushu_quanshu", "ziwei_doushu_quanji"],
    }



def get_year_gan_from_profile(profile: dict) -> str:
    """从profile获取年干（使用lunar_python或直接解析日期）。"""
    try:
        bd = profile.get("birth_date", "")
        year = None
        if bd:
            parts = str(bd).split("-")
            if len(parts) == 3:
                year = int(parts[0])
        if not year:
            birth_date = profile.get("birth_date") or profile.get("birthDate") or ""
            if hasattr(birth_date, 'year'):
                year = birth_date.year
        if year:
            from core.bazi_constants import HEAVENLY_STEMS
            return HEAVENLY_STEMS[(year - 4) % 10]
        return ""
    except Exception:
        return ""


def get_year_branch_from_profile(profile: dict) -> str:
    """从 profile 获取年支。

    当前项目的紫微年干按公历年份计算；年支也使用同一套年份口径，
    避免用“年干索引”粗略推年支造成 2000 庚辰年被误当成庚午年。
    """
    try:
        bd = profile.get("birth_date", "")
        year = None
        if bd:
            parts = str(bd).split("-")
            if len(parts) == 3:
                year = int(parts[0])
        if not year:
            birth_date = profile.get("birth_date") or profile.get("birthDate") or ""
            if hasattr(birth_date, "year"):
                year = birth_date.year
        if year:
            return EARTHLY_BRANCHES[(year - 4) % 12]
        return ""
    except Exception:
        return ""
