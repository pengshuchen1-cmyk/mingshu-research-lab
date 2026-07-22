"""Explicit four-pillar calculation driven by project-local boundary rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from core.bazi_calendar_adapter import (
    BirthInput,
    CalendarEvidence,
    JieBoundary,
    day_pillar_seed,
    jie_boundaries,
    normalize_birth_input,
)
from core.bazi_constants import EARTHLY_BRANCHES, HEAVENLY_STEMS


MONTH_BRANCH_BY_JIE = {
    "立春": "寅",
    "惊蛰": "卯",
    "清明": "辰",
    "立夏": "巳",
    "芒种": "午",
    "小暑": "未",
    "立秋": "申",
    "白露": "酉",
    "寒露": "戌",
    "立冬": "亥",
    "大雪": "子",
    "小寒": "丑",
}
MONTH_STEM_START = (2, 4, 6, 8, 0)
HOUR_STEM_START = (0, 2, 4, 6, 8)


@dataclass(frozen=True)
class Pillar:
    gan: str
    zhi: str

    @property
    def text(self) -> str:
        return f"{self.gan}{self.zhi}"


@dataclass(frozen=True)
class PillarEvidence:
    year_basis: str
    month_basis: str
    day_basis: str
    hour_basis: str
    rule_ids: tuple[str, ...]

    def public_text(self) -> str:
        return "；".join(
            (self.year_basis, self.month_basis, self.day_basis, self.hour_basis)
        )


@dataclass(frozen=True)
class FourPillarsResult:
    calendar: CalendarEvidence
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar | None
    evidence: PillarEvidence


def _year_pillar(effective_year: int) -> Pillar:
    return Pillar(
        HEAVENLY_STEMS[(effective_year - 4) % 10],
        EARTHLY_BRANCHES[(effective_year - 4) % 12],
    )


def _latest_jie(at: datetime) -> JieBoundary:
    candidates = jie_boundaries(at.year - 1) + jie_boundaries(at.year)
    eligible = [boundary for boundary in candidates if boundary.at <= at]
    if not eligible:
        raise ValueError(f"no Jie boundary before {at.isoformat()}")
    return max(eligible, key=lambda boundary: boundary.at)


def _month_pillar(year_gan: str, boundary: JieBoundary) -> Pillar:
    branch = MONTH_BRANCH_BY_JIE[boundary.name]
    month_offset = (EARTHLY_BRANCHES.index(branch) - EARTHLY_BRANCHES.index("寅")) % 12
    year_group = HEAVENLY_STEMS.index(year_gan) % 5
    stem_index = (MONTH_STEM_START[year_group] + month_offset) % 10
    return Pillar(HEAVENLY_STEMS[stem_index], branch)


def _hour_pillar(day_gan: str, hour: int) -> Pillar:
    branch_index = ((hour + 1) // 2) % 12
    day_group = HEAVENLY_STEMS.index(day_gan) % 5
    stem_index = (HOUR_STEM_START[day_group] + branch_index) % 10
    return Pillar(HEAVENLY_STEMS[stem_index], EARTHLY_BRANCHES[branch_index])


def calculate_four_pillars(
    birth: BirthInput,
    *,
    civil_datetime_override: datetime | None = None,
) -> FourPillarsResult:
    calendar = normalize_birth_input(birth)
    at = civil_datetime_override or calendar.civil_datetime
    boundary_time = at or datetime.combine(calendar.converted_solar_date, datetime.min.time())

    lichun = next(item for item in jie_boundaries(boundary_time.year) if item.name == "立春")
    effective_year = boundary_time.year if boundary_time >= lichun.at else boundary_time.year - 1
    year = _year_pillar(effective_year)

    month_boundary = _latest_jie(boundary_time)
    month = _month_pillar(year.gan, month_boundary)

    effective_day = calendar.converted_solar_date
    rolls_at_zi = at is not None and at.hour >= 23
    if rolls_at_zi:
        effective_day += timedelta(days=1)
    day_gan, day_zhi = day_pillar_seed(effective_day)
    day = Pillar(day_gan, day_zhi)

    hour = None
    if at is not None:
        hour = _hour_pillar(day.gan, at.hour)

    day_basis = (
        f"出生钟表时间已到23:00，按次日{effective_day.isoformat()}取日柱"
        if rolls_at_zi
        else f"未到23:00，按当日{effective_day.isoformat()}取日柱"
    )
    hour_basis = (
        f"按五鼠遁，以{day.gan}日和{at.hour:02d}:{at.minute:02d}确定{hour.text}"
        if at is not None and hour is not None
        else "时辰不详，不推定时柱"
    )
    evidence = PillarEvidence(
        year_basis=(
            f"以立春{lichun.at.isoformat(sep=' ')}换年，采用{effective_year}年干支"
        ),
        month_basis=(
            f"最近已过的节为{month_boundary.name}"
            f"（{month_boundary.at.isoformat(sep=' ')}），按五虎遁取月柱"
        ),
        day_basis=day_basis,
        hour_basis=hour_basis,
        rule_ids=(
            "CAL-YEAR-LICHUN",
            "CAL-MONTH-JIE",
            "CAL-DAY-ZI23",
            "PILLAR-MONTH-FIVETIGER",
            "PILLAR-HOUR-FIVERAT",
        ),
    )
    return FourPillarsResult(calendar, year, month, day, hour, evidence)
