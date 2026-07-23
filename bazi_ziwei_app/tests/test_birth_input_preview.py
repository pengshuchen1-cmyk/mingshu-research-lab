from core.birth_input_preview import BirthFormInput, build_birth_preview


def test_1999_lunar_input_builds_expected_receipt_and_pillars():
    preview = build_birth_preview(
        BirthFormInput(
            name="访客",
            gender="男",
            calendar="lunar",
            year=1999,
            month=7,
            day=1,
            is_leap_month=False,
            hour=10,
            minute=0,
            time_label="巳时",
        )
    )

    assert preview.solar_datetime == "1999-08-11 10:00"
    assert preview.pillars == ("己卯", "壬申", "乙未", "辛巳")
    assert "农历1999年七月初一" in preview.input_text
    assert "非闰月" in preview.input_text
    assert preview.chart_fingerprint == preview.chart["chart_fingerprint_v2"]


def test_same_numeric_solar_date_is_explicitly_different():
    preview = build_birth_preview(
        BirthFormInput(
            name="访客",
            gender="男",
            calendar="solar",
            year=1999,
            month=7,
            day=1,
            hour=10,
            minute=0,
            time_label="精确时间",
        )
    )

    assert preview.input_text.startswith("公历1999年7月1日")
    assert preview.pillars != ("己卯", "壬申", "乙未", "辛巳")


def test_invalid_lunar_date_does_not_produce_a_preview():
    import pytest

    with pytest.raises(ValueError, match="农历日期"):
        build_birth_preview(
            BirthFormInput(
                name="访客",
                gender="女",
                calendar="lunar",
                year=1999,
                month=2,
                day=31,
                hour=10,
                minute=0,
            )
        )


def test_paired_unknown_time_is_valid_but_partial_time_is_invalid():
    from utils.validators import validate_profile

    profile = {
        "name": "访客",
        "birth_date": "1999-07-01",
        "birth_hour": None,
        "birth_minute": None,
    }
    assert validate_profile(profile) == (True, "校验通过。")

    profile["birth_minute"] = 0
    assert validate_profile(profile) == (False, "出生小时和分钟需要同时填写。")


def test_preview_profile_and_chart_are_deeply_immutable():
    import pytest

    preview = build_birth_preview(
        BirthFormInput(
            name="访客",
            gender="男",
            calendar="solar",
            year=1999,
            month=7,
            day=1,
            hour=10,
            minute=0,
        )
    )

    with pytest.raises(TypeError):
        preview.profile["name"] = "篡改"
    with pytest.raises(TypeError):
        preview.chart["pillars"]["year"]["pillar"] = "篡改"
    with pytest.raises(AttributeError):
        preview.chart["pillar_evidence"]["rule_ids"].append("篡改")
