from __future__ import annotations

import re

import pandas as pd

from src.schemas import ClientRequirements


COUNTRY_ALIASES = {
    "korea": "korea",
    "корея": "korea",
    "south korea": "korea",
    "china": "china",
    "китай": "china",
    "europe": "europe",
    "европа": "europe",
}

BODY_ALIASES = {
    "suv": "suv",
    "crossover": "suv",
    "кроссовер": "suv",
    "внедорожник": "suv",
    "sedan": "sedan",
    "седан": "sedan",
    "minivan": "minivan",
    "минивэн": "minivan",
    "wagon": "wagon",
    "универсал": "wagon",
    "liftback": "liftback",
    "лифтбек": "liftback",
}


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _normalize_country(value: object) -> str:
    text = _normalize_text(value)
    return COUNTRY_ALIASES.get(text, text)


def _normalize_body(value: object) -> str:
    text = _normalize_text(value)
    return BODY_ALIASES.get(text, text)


def _normalize_list(values: list[str], kind: str = "text") -> set[str]:
    if kind == "country":
        return {_normalize_country(value) for value in values}
    if kind == "body":
        return {_normalize_body(value) for value in values}
    return {_normalize_text(value) for value in values}


def _priority_score(row: pd.Series, priority: str) -> int:
    if priority in {"comfort", "liquidity", "reliability", "status", "equipment"}:
        return 5 if int(row.get(priority, 0) or 0) >= 4 else 0
    if priority == "low_risk":
        reliability = int(row.get("reliability", 0) or 0)
        liquidity = int(row.get("liquidity", 0) or 0)
        return 5 if reliability >= 4 and liquidity >= 4 else 0
    if priority == "family":
        body = _normalize_body(row.get("body_type"))
        comfort = int(row.get("comfort", 0) or 0)
        return 5 if body in {"suv", "minivan", "wagon"} and comfort >= 4 else 0
    if priority == "dynamics":
        engine = _normalize_text(row.get("engine"))
        return 5 if any(token in engine for token in ["3.0", "v6", "hybrid", "electric", "phev"]) else 0
    return 0


def _ensure_numeric(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "year",
        "mileage_km",
        "price_rub",
        "total_price_rub",
        "liquidity",
        "comfort",
        "reliability",
        "status",
        "equipment",
    ]
    result = df.copy()
    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0).astype(int)
    return result


def filter_and_rank_cars(cars_df: pd.DataFrame, req: ClientRequirements) -> pd.DataFrame:
    df = _ensure_numeric(cars_df)
    if df.empty:
        return df.assign(score=pd.Series(dtype=int))

    if req.budget_rub:
        df = df[df["total_price_rub"] <= int(req.budget_rub * 1.07)]

    excluded_countries = _normalize_list(req.excluded_countries, "country")
    if excluded_countries:
        df = df[~df["country"].map(_normalize_country).isin(excluded_countries)]

    excluded_brands = _normalize_list(req.excluded_brands)
    if excluded_brands:
        df = df[~df["brand"].map(_normalize_text).isin(excluded_brands)]

    if req.min_year:
        df = df[df["year"] >= req.min_year]

    if req.max_mileage_km:
        df = df[df["mileage_km"] <= req.max_mileage_km]

    if df.empty:
        return df.assign(score=pd.Series(dtype=int))

    preferred_countries = _normalize_list(req.countries, "country")
    preferred_brands = _normalize_list(req.preferred_brands)
    wanted_body = _normalize_body(req.body_type) if req.body_type else None

    def score_row(row: pd.Series) -> int:
        score = 0
        total_price = int(row.get("total_price_rub", 0) or 0)

        if req.budget_rub:
            if total_price <= req.budget_rub:
                score += 30
            elif total_price <= int(req.budget_rub * 1.07):
                score += 15
            else:
                score -= 30

        if wanted_body and _normalize_body(row.get("body_type")) == wanted_body:
            score += 15
        elif wanted_body:
            score -= 10

        if preferred_countries and _normalize_country(row.get("country")) in preferred_countries:
            score += 10

        if preferred_brands and _normalize_text(row.get("brand")) in preferred_brands:
            score += 10

        if req.min_year and int(row.get("year", 0) or 0) >= req.min_year:
            score += 10

        if req.max_mileage_km and int(row.get("mileage_km", 0) or 0) <= req.max_mileage_km:
            score += 10

        for priority in req.priorities:
            score += _priority_score(row, priority)

        return max(0, min(100, score))

    ranked = df.copy()
    ranked["score"] = ranked.apply(score_row, axis=1)
    return ranked.sort_values(
        by=["score", "total_price_rub", "year"],
        ascending=[False, True, False],
    ).head(7).reset_index(drop=True)
