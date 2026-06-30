"""
\u5927\u9650\u57fa\u7840\u7ed3\u6784 — v1.2-E

\u89c4\u5219:
- \u9633\u7537\u987a\u884c\uff0c\u9634\u5973\u987a\u884c
- \u9634\u7537\u9006\u884c\uff0c\u9633\u5973\u9006\u884c
- \u8d77\u9650\u5e74\u9f84\u57fa\u4e8e\u4e94\u884c\u5c40
    
\u6765\u6e90: \u300a\u7d2b\u5fae\u6597\u6570\u5168\u4e66\u300b\u5927\u9650\u7ae0
"""

from __future__ import annotations

BRANCHES = ["\u5b50","\u4e11","\u5bc5","\u536f","\u8fb0","\u5df3","\u5348","\u672a","\u7533","\u9149","\u620c","\u4ea5"]
PALACE_NAMES = ["\u547d\u5bab","\u5144\u5f1f\u5bab","\u592b\u59bb\u5bab","\u5b50\u5973\u5bab","\u8d22\u5e1b\u5bab","\u75be\u5384\u5bab","\u8fc1\u79fb\u5bab","\u4ea4\u53cb\u5bab","\u5b98\u7984\u5bab","\u7530\u5b85\u5bab","\u798f\u5fb7\u5bab","\u7236\u6bcd\u5bab"]

DAXIAN_AGE_MAP = {"\u6c34":2,"\u6728":3,"\u91d1":4,"\u571f":5,"\u706b":6}


def _idx(b): return BRANCHES.index(b) if b in BRANCHES else -1


def calculate_daxian(gender: str, birth_year_gan: str, five_element_number: int,
                     life_palace_branch: str, body_palace_branch: str,
                     main_stars_by_palace: dict) -> dict:
    """\u8ba1\u7b97\u5927\u9650\u57fa\u7840\u7ed3\u6784"""
    if not all([gender, birth_year_gan, five_element_number, life_palace_branch]):
        return {"daxian_ready": False, "error": "\u8f93\u5165\u53c2\u6570\u4e0d\u8db3"}

    is_yang = birth_year_gan in "\u7532\u4e19\u620a\u5e9a\u58ec"
    is_male = gender == "\u7537"
    forward = (is_yang and is_male) or (not is_yang and not is_male)

    start_age = DAXIAN_AGE_MAP.get({4:"\u91d1",3:"\u6728",2:"\u6c34",5:"\u571f",6:"\u706b"}.get(five_element_number,"\u6c34"), 4)
    life_idx = _idx(life_palace_branch)

    stages = []
    for i in range(12):
        if forward:
            palace_idx = (life_idx + i) % 12
        else:
            palace_idx = (life_idx - i) % 12
        palace_name = PALACE_NAMES[palace_idx]
        branch = BRANCHES[palace_idx]
        start = start_age + i * 10
        end = start + 9
        ms = main_stars_by_palace.get(palace_name, [])
        stages.append({
            "age_range": f"{start}-{end}",
            "palace": palace_name,
            "branch": branch,
            "main_stars": ms,
            "summary": f"{palace_name}\u5927\u9650{start}-{end}\u5c81\uff0c\u6b64\u9636\u6bb5\u4e8b\u4e1a\u3001\u8d22\u5bcc\u3001\u5173\u7cfb\u53ef\u7ed3\u5408\u8be5\u5bab\u4e3b\u661f\u89c2\u5bdf\u3002",
            "boundary": "\u5f53\u524d\u4e3a\u5927\u9650\u57fa\u7840\u7ed3\u6784\uff0c\u5c1a\u672a\u52a0\u5165\u590d\u6742\u98de\u5316\u65ad\u4e8b\u3002",
        })

    return {
        "daxian_ready": True,
        "start_age": start_age,
        "forward": forward,
        "stages": stages,
        "source_ids": ["ziwei_doushu_quanshu", "ziwei_doushu_quanji"],
        "basis": "\u57fa\u4e8e\u300a\u7d2b\u5fae\u6597\u6570\u5168\u4e66\u300b\u5927\u9650\u7ae0\uff0c\u9633\u7537\u9634\u5973\u987a\u884c\uff0c\u9634\u7537\u9633\u5973\u9006\u884c\uff0c\u8d77\u9650\u5e74\u9f84\u57fa\u4e8e\u4e94\u884c\u5c40\u3002",
    }
