"""输入校验工具。"""


def validate_profile(profile: dict) -> tuple[bool, str]:
    """
    校验命盘用户资料。
    """
    if not str(profile.get("name", "")).strip():
        return False, "姓名不能为空。"
    if not profile.get("birth_date"):
        return False, "出生日期不能为空。"
    try:
        birth_hour = int(profile.get("birth_hour", -1))
        birth_minute = int(profile.get("birth_minute", -1))
    except (TypeError, ValueError):
        return False, "出生时间格式不正确。"
    if birth_hour < 0 or birth_hour > 23:
        return False, "出生小时必须在 0-23 之间。"
    if birth_minute < 0 or birth_minute > 59:
        return False, "出生分钟必须在 0-59 之间。"
    return True, "校验通过。"
