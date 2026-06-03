from __future__ import annotations

from src.extraction import parse_requirements_json


def test_json_with_text_around_it_is_extracted() -> None:
    raw = """
    Here is the JSON:
    {
      "budget_rub": 8000000,
      "body_type": "SUV",
      "countries": ["Korea", "Europe"],
      "excluded_countries": ["China"],
      "preferred_brands": [],
      "excluded_brands": [],
      "priorities": ["comfort", "liquidity"],
      "max_mileage_km": null,
      "min_year": 2021,
      "client_profile": "family premium client",
      "missing_info": []
    }
    Done.
    """

    result = parse_requirements_json(raw)

    assert result.budget_rub == 8000000
    assert result.body_type == "SUV"
    assert result.excluded_countries == ["China"]
    assert result.priorities == ["comfort", "liquidity"]


def test_invalid_json_returns_safe_structure() -> None:
    result = parse_requirements_json("not a json at all")

    assert result.budget_rub is None
    assert result.missing_info


def test_fallback_extracts_obvious_russian_client_request() -> None:
    result = parse_requirements_json(
        "LLM_ERROR: test",
        "Нужен большой семейный автомобиль до 7 млн, желательно свежий, "
        "с богатой комплектацией и без лишних рисков.",
    )

    assert result.budget_rub == 7_000_000
    assert "family" in result.priorities
    assert "equipment" in result.priorities
    assert "low_risk" in result.priorities
