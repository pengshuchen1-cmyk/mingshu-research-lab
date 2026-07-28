def synthetic_chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {
            "gender": "男",
            "birth_date": "1994-09-23",
            "birth_hour": 18,
            "birth_minute": 0,
        }
    )
