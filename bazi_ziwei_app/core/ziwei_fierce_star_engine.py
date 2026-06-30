"""
\u715e\u661f\u843d\u5bab\u7b97\u6cd5 — v1.2-E

\u64ce\u7f8a/\u9640\u7f57: \u7984\u5b58\u524d\u540e\u4e00\u5bab
\u706b\u661f/\u94c3\u661f: \u5e74\u652f+\u65f6\u652f lookup
\u5730\u7a7a/\u5730\u52ab: \u5e74\u8d77
\u6765\u6e90: \u300a\u7d2b\u5fae\u6597\u6570\u5168\u4e66\u300b\u5b89\u661f\u6cd5
"""

BRANCHES = ["\u5b50","\u4e11","\u5bc5","\u536f","\u8fb0","\u5df3","\u5348","\u672a","\u7533","\u9149","\u620c","\u4ea5"]

def _idx(b): return BRANCHES.index(b) if b in BRANCHES else -1

# \u7984\u5b58: \u7532\u5bc5\u4e59\u536f\u4e19\u620c\u5df3\u5df3\u4e01\u5348\u620c\u5df3\u5df3\u5df1\u5df3\u5e9a\u7533\u8f9b\u9149\u58ec\u4ea5\u7678\u5b50
LUCUN: dict = {"\u7532":"\u5bc5","\u4e59":"\u536f","\u4e19":"\u5df3","\u4e01":"\u5348","\u620a":"\u5df3","\u5df1":"\u5348","\u5e9a":"\u7533","\u8f9b":"\u9149","\u58ec":"\u4ea5","\u7678":"\u5b50"}

def get_lucun(year_gan: str) -> str:
    return LUCUN.get(year_gan, "")


def calculate_qingyang(year_gan: str) -> dict:
    lu = get_lucun(year_gan)
    if not lu: return {"star":"\u64ce\u7f8a","placement_ready":False}
    idx = (_idx(lu) + 1) % 12
    return {"star":"\u64ce\u7f8a","branch":BRANCHES[idx],"method":"lucun_forward","placement_ready":True,
            "source_ids":["ziwei_doushu_quanshu"],"basis":"\u64ce\u7f8a\u5728\u7984\u5b58\u987a\u9488\u524d\u4e00\u5bab\u3002"}


def calculate_tuoluo(year_gan: str) -> dict:
    lu = get_lucun(year_gan)
    if not lu: return {"star":"\u9640\u7f57","placement_ready":False}
    idx = (_idx(lu) - 1) % 12
    return {"star":"\u9640\u7f57","branch":BRANCHES[idx],"method":"lucun_backward","placement_ready":True,
            "source_ids":["ziwei_doushu_quanshu"],"basis":"\u9640\u7f57\u5728\u7984\u5b58\u9006\u9488\u540e\u4e00\u5bab\u3002"}


# \u706b\u661f/\u94c3\u661f \u5e74\u652f+\u65f6\u652f\u67e5\u8868
# Key: (\u5e74\u652f, \u65f6\u652f) -> branch index
    key = (year_branch, hour_branch)
    if key in HUOXING_MAP:
        idx = HUOXING_MAP[key]
        return {"star":"\u706b\u661f","branch":BRANCHES[idx],"method":"year_hour_lookup","placement_ready":True,
                "source_ids":["ziwei_doushu_quanshu"],"basis":"\u706b\u661f\u57fa\u4e8e\u5e74\u652f\u548c\u65f6\u652f\u67e5\u8868\u3002\u5f53\u524d\u4ec5\u652f\u6301\u90e8\u5206\u7ec4\u5408\u3002"}
    return {"star":"\u706b\u661f","placement_ready":False,"note":"\u706b\u661f\u67e5\u8868\u672a\u5b8c\u5168\u5b9e\u73b0"}


def calculate_lingxing(year_branch: str, hour_branch: str) -> dict:
    key = (year_branch, hour_branch)
    if key in LINGXING_MAP:
        idx = LINGXING_MAP[key]
        return {"star":"\u94c3\u661f","branch":BRANCHES[idx],"method":"year_hour_lookup","placement_ready":True,
                "source_ids":["ziwei_doushu_quanshu"],"basis":"\u94c3\u661f\u57fa\u4e8e\u5e74\u652f\u548c\u65f6\u652f\u67e5\u8868\u3002\u5f53\u524d\u4ec5\u652f\u6301\u90e8\u5206\u7ec4\u5408\u3002"}
    return {"star":"\u94c3\u661f","placement_ready":False,"note":"\u94c3\u661f\u67e5\u8868\u672a\u5b8c\u5168\u5b9e\u73b0"}


def calculate_dikong(year_gan: str) -> dict:
    "\u5730\u7a7a: \u4ea5\u5bab\u8d77\u5b50\u5e74\uff0c\u9006\u65f6\u9488\u6570\u5230\u751f\u5e74"
    start = 11  # \u4ea5
    gan_idx = "\u7532\u4e59\u4e19\u4e01\u620a\u5df1\u5e9a\u8f9b\u58ec\u7678".index(year_gan) if year_gan else 0
    offset = gan_idx % 12
    idx = (start - offset) % 12
    return {"star":"\u5730\u7a7a","branch":BRANCHES[idx],"method":"year_gan_backward","placement_ready":True,
            "source_ids":["ziwei_doushu_quanshu"],"basis":"\u5730\u7a7a\u4ece\u4ea5\u5bab\u8d77\u5b50\u5e74\uff0c\u9006\u65f6\u9488\u6570\u5230\u751f\u5e74\u5e72\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_dijie(year_gan: str) -> dict:
    "\u5730\u52ab: \u5df3\u5bab\u8d77\u5b50\u5e74\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u5e74"
    start = 5  # \u5df3
    gan_idx = "\u7532\u4e59\u4e19\u4e01\u620a\u5df1\u5e9a\u8f9b\u58ec\u7678".index(year_gan) if year_gan else 0
    offset = gan_idx % 12
    idx = (start + offset) % 12
    return {"star":"\u5730\u52ab","branch":BRANCHES[idx],"method":"year_gan_forward","placement_ready":True,
            "source_ids":["ziwei_doushu_quanshu"],"basis":"\u5730\u52ab\u4ece\u5df3\u5bab\u8d77\u5b50\u5e74\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u5e74\u5e72\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_all_fierce_stars(year_gan: str, year_branch: str, hour_branch: str) -> dict:
    return {
        "placement_ready": True,
        "stars": {
            "qingyang": calculate_qingyang(year_gan),
            "tuoluo": calculate_tuoluo(year_gan),
            "huoxing": calculate_huoxing(year_branch, hour_branch),
            "lingxing": calculate_lingxing(year_branch, hour_branch),
            "dikong": calculate_dikong(year_gan),
            "dijie": calculate_dijie(year_gan),
        },
        "source_ids": ["ziwei_doushu_quanshu"],
    }

# 火星/铃星 年支+时支查表（完整 12×12 组合）
# 规则（《紫微斗数全书》）：
# 火星: 子午卯酉卯宫起、寅申巳亥酉宫起、辰戌丑未子宫起
# 铃星: 子午卯酉酉宫起、寅申巳亥巳宫起、辰戌丑未午宫起

def _build_huoxing_table():
    sm = {"子":"卯","午":"卯","卯":"卯","酉":"卯",
          "寅":"酉","申":"酉","巳":"酉","亥":"酉",
          "辰":"子","戌":"子","丑":"子","未":"子"}
    return {(yb, hb): (BRANCHES.index(sm[yb]) + ho) % 12
            for yb in sm for ho, hb in enumerate(BRANCHES)}

def _build_lingxing_table():
    sm = {"子":"酉","午":"酉","卯":"酉","酉":"酉",
          "寅":"巳","申":"巳","巳":"巳","亥":"巳",
          "辰":"午","戌":"午","丑":"午","未":"午"}
    return {(yb, hb): (BRANCHES.index(sm[yb]) + ho) % 12
            for yb in sm for ho, hb in enumerate(BRANCHES)}

HUOXING_MAP = _build_huoxing_table()
LINGXING_MAP = _build_lingxing_table()


def calculate_huoxing(year_branch: str, hour_branch: str) -> dict:
    key = (year_branch, hour_branch)
    if key in HUOXING_MAP:
        idx = HUOXING_MAP[key]
        return {"star":"火星","branch":BRANCHES[idx],"method":"year_hour_lookup","placement_ready":True,
                "source_ids":["ziwei_doushu_quanshu"],
                "basis":"火星基于年支和时支查表。已补全12年支×12时支共144组合。"}
    return {"star":"火星","placement_ready":False,"note":"火星查表未完全实现"}


def calculate_lingxing(year_branch: str, hour_branch: str) -> dict:
    key = (year_branch, hour_branch)
    if key in LINGXING_MAP:
        idx = LINGXING_MAP[key]
        return {"star":"铃星","branch":BRANCHES[idx],"method":"year_hour_lookup","placement_ready":True,
                "source_ids":["ziwei_doushu_quanshu"],
                "basis":"铃星基于年支和时支查表。已补全12年支×12时支共144组合。"}
    return {"star":"铃星","placement_ready":False,"note":"铃星查表未完全实现"}
