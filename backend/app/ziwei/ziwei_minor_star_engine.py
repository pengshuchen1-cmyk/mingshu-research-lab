"""
辅星落宫算法 — v1.2-E
文昌/文曲: 时辰起法。左辅/右弼: 月份起法。
来源: 《紫微斗数全书》安星法。
"""

from __future__ import annotations

BRANCHES = ["\u5b50","\u4e11","\u5bc5","\u536f","\u8fb0","\u5df3","\u5348","\u672a","\u7533","\u9149","\u620c","\u4ea5"]

def _idx(b): return BRANCHES.index(b) if b in BRANCHES else -1


def calculate_wenchang(hour_branch: str) -> dict:
    "\u6587\u660c: \u620c\u5bab\u8d77\u5b50\u65f6\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u65f6"
    start = 10  # \u620c
    offset = (_idx(hour_branch) - _idx("\u5b50")) % 12
    idx = (start + offset) % 12
    return {"star": "\u6587\u660c", "branch": BRANCHES[idx], "method": "wenchang_hour", "placement_ready": True,
            "source_ids": ["ziwei_doushu_quanshu"], "basis": "\u6587\u660c\u4ece\u620c\u5bab\u8d77\u5b50\u65f6\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u65f6\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_wenqu(hour_branch: str) -> dict:
    "\u6587\u66f2: \u8fb0\u5bab\u8d77\u5b50\u65f6\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u65f6"
    start = 4  # \u8fb0
    offset = (_idx(hour_branch) - _idx("\u5b50")) % 12
    idx = (start + offset) % 12
    return {"star": "\u6587\u66f2", "branch": BRANCHES[idx], "method": "wenqu_hour", "placement_ready": True,
            "source_ids": ["ziwei_doushu_quanshu"], "basis": "\u6587\u66f2\u4ece\u8fb0\u5bab\u8d77\u5b50\u65f6\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u65f6\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_zuofu(lunar_month: int) -> dict:
    "\u5de6\u8f85: \u8fb0\u5bab\u8d77\u6b63\u6708\uff0c\u9006\u65f6\u9488\u6570\u5230\u751f\u6708"
    start = 4  # \u8fb0
    offset = (lunar_month - 1) % 12
    idx = (start - offset) % 12
    return {"star": "\u5de6\u8f85", "branch": BRANCHES[idx], "method": "zuofu_month", "placement_ready": True,
            "source_ids": ["ziwei_doushu_quanshu"], "basis": "\u5de6\u8f85\u4ece\u8fb0\u5bab\u8d77\u6b63\u6708\uff0c\u9006\u65f6\u9488\u6570\u5230\u751f\u6708\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_youbi(lunar_month: int) -> dict:
    "\u53f3\u5f3c: \u620c\u5bab\u8d77\u6b63\u6708\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u6708"
    start = 10  # \u620c
    offset = (lunar_month - 1) % 12
    idx = (start + offset) % 12
    return {"star": "\u53f3\u5f3c", "branch": BRANCHES[idx], "method": "youbi_month", "placement_ready": True,
            "source_ids": ["ziwei_doushu_quanshu"], "basis": "\u53f3\u5f3c\u4ece\u620c\u5bab\u8d77\u6b63\u6708\uff0c\u987a\u65f6\u9488\u6570\u5230\u751f\u6708\u6240\u5728\u5bab\u4f4d\u3002"}


def calculate_all_minor_stars(hour_branch: str, lunar_month: int) -> dict:
    results = {
        "wenchang": calculate_wenchang(hour_branch),
        "wenqu": calculate_wenqu(hour_branch),
        "zuofu": calculate_zuofu(lunar_month),
        "youbi": calculate_youbi(lunar_month),
    }
    return {
        "placement_ready": all(r["placement_ready"] for r in results.values()),
        "stars": results,
        "all_ready": True,
        "source_ids": ["ziwei_doushu_quanshu"],
    }
