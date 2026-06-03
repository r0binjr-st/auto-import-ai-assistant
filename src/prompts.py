from __future__ import annotations

import json

import pandas as pd

from src.schemas import ClientRequirements


def build_extraction_prompt(client_request: str) -> str:
    return f"""
Extract structured requirements from a Russian client request about importing a premium car.

Return ONLY valid JSON. Do not use markdown. Do not add text before or after JSON.
Do not invent a budget if it is not present. If data is missing, use null or an empty list.

Allowed body_type values: SUV, sedan, minivan, wagon, liftback.
Allowed country values: Korea, China, Europe.
Allowed priorities: comfort, liquidity, reliability, status, dynamics, family, low_risk, equipment.

JSON schema:
{{
  "budget_rub": int or null,
  "body_type": string or null,
  "countries": list[str],
  "excluded_countries": list[str],
  "preferred_brands": list[str],
  "excluded_brands": list[str],
  "priorities": list[str],
  "max_mileage_km": int or null,
  "min_year": int or null,
  "client_profile": string or null,
  "missing_info": list[str]
}}

Client request:
{client_request}
""".strip()


def build_analysis_prompt(
    client_request: str,
    requirements: ClientRequirements,
    top_cars: pd.DataFrame,
) -> str:
    cars_json = top_cars.to_json(orient="records", force_ascii=False)
    requirements_json = json.dumps(requirements.model_dump(), ensure_ascii=False, indent=2)
    return f"""
You are an assistant for a manager who imports premium cars to Russia.
Use ONLY the client request, extracted requirements, and CSV rows below.
Do not invent prices, years, mileage, equipment, market facts, delivery terms, customs fees, or availability.
If a risk is not present in the data, phrase it as something to verify, not as a fact.
Answer in Russian Markdown using exactly the requested sections.

Client request:
{client_request}

Extracted requirements:
{requirements_json}

Top cars from CSV:
{cars_json}

Required Markdown structure:
## Summary для менеджера

## Топ-3 варианта

### 1. Brand Model
- Почему подходит:
- Сильные стороны:
- Риски:
- Что проверить:

## Что уточнить у клиента

## Сообщение клиенту в Telegram
""".strip()
