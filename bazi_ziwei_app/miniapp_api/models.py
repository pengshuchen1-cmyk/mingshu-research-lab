"""小程序 API 输入模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProfilePayload(BaseModel):
    """与现有统一出生资料表单一致的输入。"""

    name: str = Field(default="访客", max_length=40)
    gender: Literal["男", "女"] = "男"
    calendar_type: Literal["solar", "lunar"] = "solar"
    birth_date: str
    birth_hour: int | None = Field(default=10, ge=0, le=23)
    birth_minute: int | None = Field(default=0, ge=0, le=59)
    birth_place: str = Field(default="", max_length=80)
    is_leap_month: bool = False
    time_known: bool = True
    note: str = Field(default="", max_length=500)

    @field_validator("birth_minute")
    @classmethod
    def minute_matches_hour(cls, value: int | None, info):
        hour = info.data.get("birth_hour")
        if (hour is None) != (value is None):
            raise ValueError("出生小时和分钟需要同时填写")
        return value

    def to_profile(self) -> dict:
        hour = self.birth_hour if self.time_known else None
        minute = self.birth_minute if self.time_known else None
        profile = {
            "name": self.name.strip() or "访客",
            "gender": self.gender,
            "calendar_type": self.calendar_type,
            "birth_date": self.birth_date,
            "birth_hour": hour,
            "birth_minute": minute,
            "birth_place": self.birth_place.strip(),
            "is_leap_month": bool(self.is_leap_month and self.calendar_type == "lunar"),
            "time_known": bool(self.time_known),
            "time_mode": "china_standard",
            "use_solar_time": False,
            "use_true_solar_time": False,
            "birth_longitude": None,
            "note": self.note.strip(),
        }
        if self.calendar_type == "lunar":
            profile["lunar_birth_date"] = self.birth_date
        return profile


class AskPayload(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CompatibilityPayload(BaseModel):
    first_profile_id: int | None = None
    second_profile_id: int | None = None
    first_profile: ProfilePayload | None = None
    second_profile: ProfilePayload | None = None


class ArchiveUpdatePayload(BaseModel):
    name: str | None = Field(default=None, max_length=40)
    birth_place: str | None = Field(default=None, max_length=80)
    note: str | None = Field(default=None, max_length=500)


class ImportPayload(BaseModel):
    payload: str = Field(min_length=2)


class SettingsPayload(BaseModel):
    report_length: Literal["简洁版", "标准版", "详细版"] = "标准版"
    show_technical_details: bool = False
    show_disclaimer: bool = True
    default_export_format: Literal["Markdown", "TXT", "PDF"] = "Markdown"
    enable_quality_check: bool = True

