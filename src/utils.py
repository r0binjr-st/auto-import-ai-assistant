from __future__ import annotations

import json

import pandas as pd

from src.schemas import ClientRequirements


def format_rub(value: int | None) -> str:
    if value is None:
        return "не указан"
    return f"{value:,} ₽".replace(",", " ")


def build_download_markdown(
    client_request: str,
    requirements: ClientRequirements,
    top_cars: pd.DataFrame,
    analysis_md: str,
) -> str:
    cars_json = top_cars.to_json(orient="records", force_ascii=False, indent=2)
    requirements_json = json.dumps(requirements.model_dump(), ensure_ascii=False, indent=2)
    return f"""# Auto Import AI Assistant

## Запрос клиента
{client_request}

## Извлеченные требования
```json
{requirements_json}
```

## Подходящие автомобили
```json
{cars_json}
```

{analysis_md}
"""
