from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


ALLOWED_PRIORITIES = {
    "comfort",
    "liquidity",
    "reliability",
    "status",
    "dynamics",
    "family",
    "low_risk",
    "equipment",
}


class ClientRequirements(BaseModel):
    budget_rub: int | None = None
    body_type: str | None = None
    countries: list[str] = Field(default_factory=list)
    excluded_countries: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    max_mileage_km: int | None = None
    min_year: int | None = None
    client_profile: str | None = None
    missing_info: list[str] = Field(default_factory=list)

    @field_validator(
        "countries",
        "excluded_countries",
        "preferred_brands",
        "excluded_brands",
        "priorities",
        "missing_info",
        mode="before",
    )
    @classmethod
    def _list_or_empty(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("priorities")
    @classmethod
    def _filter_priorities(cls, priorities: list[str]) -> list[str]:
        normalized = [str(item).strip().lower() for item in priorities if str(item).strip()]
        return [item for item in normalized if item in ALLOWED_PRIORITIES]

    @field_validator("budget_rub", "max_mileage_km", "min_year", mode="before")
    @classmethod
    def _positive_int_or_none(cls, value):
        if value in ("", None):
            return None
        try:
            parsed = int(float(str(value).replace(" ", "").replace("_", "")))
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None
