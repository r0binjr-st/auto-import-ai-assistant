from __future__ import annotations

import pandas as pd

from src.llm import call_llm
from src.prompts import build_analysis_prompt
from src.schemas import ClientRequirements


def _fallback_analysis(
    client_request: str,
    requirements: ClientRequirements,
    top_cars: pd.DataFrame,
    error: str | None = None,
) -> str:
    if top_cars.empty:
        top_block = "Подходящих вариантов в текущем CSV не найдено."
    else:
        items = []
        for index, row in top_cars.head(3).iterrows():
            items.append(
                f"### {index + 1}. {row['brand']} {row['model']}\n"
                f"- Почему подходит: score {row.get('score', 0)} по фильтрам Python.\n"
                f"- Сильные стороны: {row.get('pros', 'уточнить по карточке')}.\n"
                f"- Риски: {row.get('cons', 'проверить состояние и историю')}.\n"
                f"- Что проверить: {row.get('manager_notes', 'документы, историю, комплектацию и финальную стоимость')}."
            )
        top_block = "\n\n".join(items)

    error_note = f"\n\n> LLM-анализ недоступен: {error}" if error else ""
    return f"""## Summary для менеджера
Запрос обработан по доступным данным CSV. Извлеченные требования: бюджет {requirements.budget_rub or "не указан"}, кузов {requirements.body_type or "не указан"}, приоритеты {", ".join(requirements.priorities) or "не указаны"}.
{error_note}

## Топ-3 варианта
{top_block}

## Что уточнить у клиента
- Готовность рассматривать альтернативные страны и кузовы.
- Допустимый пробег, год и комплектацию.
- Нужен ли акцент на ликвидности, статусе или минимальном риске.

## Сообщение клиенту в Telegram
Здравствуйте! Я предварительно отобрал варианты по вашему запросу из актуального CSV. Есть несколько подходящих автомобилей, но перед финальным предложением стоит уточнить желаемый год, пробег и приоритеты по комплектации.
"""


def generate_manager_analysis(
    client_request: str,
    requirements: ClientRequirements,
    top_cars: pd.DataFrame,
    model: str | None = None,
) -> str:
    prompt = build_analysis_prompt(client_request, requirements, top_cars)
    response = call_llm(prompt, model=model, temperature=0.2)
    if not response or response.startswith("LLM_ERROR"):
        return _fallback_analysis(client_request, requirements, top_cars, error=response)
    return response
