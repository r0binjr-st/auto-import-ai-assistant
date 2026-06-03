from __future__ import annotations

import pandas as pd

from src.filtering import filter_and_rank_cars
from src.schemas import ClientRequirements


def _cars_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "brand": "Genesis",
                "model": "GV70",
                "country": "Korea",
                "body_type": "SUV",
                "year": 2022,
                "mileage_km": 30000,
                "price_rub": 5000000,
                "total_price_rub": 7000000,
                "engine": "2.5 turbo",
                "drivetrain": "AWD",
                "pros": "comfort",
                "cons": "none",
                "liquidity": 5,
                "comfort": 5,
                "reliability": 4,
                "status": 5,
                "equipment": 5,
                "manager_notes": "check",
            },
            {
                "brand": "BMW",
                "model": "5 Series",
                "country": "Europe",
                "body_type": "sedan",
                "year": 2022,
                "mileage_km": 35000,
                "price_rub": 5200000,
                "total_price_rub": 7200000,
                "engine": "2.0 petrol",
                "drivetrain": "RWD",
                "pros": "status",
                "cons": "service",
                "liquidity": 5,
                "comfort": 5,
                "reliability": 4,
                "status": 5,
                "equipment": 4,
                "manager_notes": "diagnostics",
            },
            {
                "brand": "Li Auto",
                "model": "L9",
                "country": "China",
                "body_type": "SUV",
                "year": 2023,
                "mileage_km": 20000,
                "price_rub": 5400000,
                "total_price_rub": 9000000,
                "engine": "range extender",
                "drivetrain": "AWD",
                "pros": "family",
                "cons": "liquidity",
                "liquidity": 4,
                "comfort": 5,
                "reliability": 4,
                "status": 4,
                "equipment": 5,
                "manager_notes": "battery",
            },
        ]
    )


def test_car_more_than_seven_percent_above_budget_is_filtered_out() -> None:
    req = ClientRequirements(budget_rub=8000000)
    result = filter_and_rank_cars(_cars_df(), req)

    assert "L9" not in set(result["model"])


def test_matching_body_type_gets_higher_score() -> None:
    req = ClientRequirements(body_type="SUV")
    result = filter_and_rank_cars(_cars_df(), req)

    suv_score = result[result["model"] == "GV70"]["score"].iloc[0]
    sedan_score = result[result["model"] == "5 Series"]["score"].iloc[0]
    assert suv_score > sedan_score


def test_excluded_country_is_not_returned() -> None:
    req = ClientRequirements(excluded_countries=["China"])
    result = filter_and_rank_cars(_cars_df(), req)

    assert "China" not in set(result["country"])


def test_preferred_brand_increases_score() -> None:
    base = filter_and_rank_cars(_cars_df(), ClientRequirements())
    preferred = filter_and_rank_cars(_cars_df(), ClientRequirements(preferred_brands=["BMW"]))

    base_score = base[base["brand"] == "BMW"]["score"].iloc[0]
    preferred_score = preferred[preferred["brand"] == "BMW"]["score"].iloc[0]
    assert preferred_score > base_score
