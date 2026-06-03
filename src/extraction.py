from __future__ import annotations

import json
import re

from pydantic import ValidationError

from src.llm import call_llm
from src.prompts import build_extraction_prompt
from src.schemas import ClientRequirements


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _extract_budget(text: str) -> int | None:
    normalized = text.lower().replace(",", ".")
    million_match = re.search(
        r"(?:до|бюджет|в пределах|около)?\s*(\d+(?:\.\d+)?)\s*(?:млн|миллион)",
        normalized,
    )
    if million_match:
        return int(float(million_match.group(1)) * 1_000_000)

    rub_match = re.search(
        r"(?:до|бюджет|в пределах)?\s*(\d[\d\s]{5,})\s*(?:руб|₽|р\b)?",
        normalized,
    )
    if rub_match:
        return int(re.sub(r"\s+", "", rub_match.group(1)))

    return None


def _extract_max_mileage(text: str) -> int | None:
    normalized = text.lower().replace(",", ".")
    match = re.search(
        r"(?:до|не более|max|макс\.?)\s*(\d{1,3})(?:\s*[-–]?\s*)?(?:тыс|000)\s*(?:км|пробег)",
        normalized,
    )
    if match:
        return int(match.group(1)) * 1_000

    match = re.search(r"(?:пробег|км)\D{0,20}(?:до|не более|max|макс\.?)\s*(\d[\d\s]{3,})", normalized)
    if match:
        return int(re.sub(r"\s+", "", match.group(1)))

    return None


def _extract_min_year(text: str) -> int | None:
    normalized = text.lower()
    match = re.search(r"(?:от|с|не старше)\s*(20\d{2})", normalized)
    if match:
        return int(match.group(1))

    match = re.search(r"(20\d{2})\s*(?:года|год|г\.?)\s*(?:и моложе|или свежее|и свежее)", normalized)
    if match:
        return int(match.group(1))

    return None


def _heuristic_extract(client_request: str, raw_response: str = "") -> ClientRequirements:
    text = client_request.lower()
    req = ClientRequirements()

    req.budget_rub = _extract_budget(text)
    req.max_mileage_km = _extract_max_mileage(text)
    req.min_year = _extract_min_year(text)

    body_keywords = [
        ("SUV", ["suv", "кроссовер", "внедорожник", "джип", "паркетник"]),
        ("sedan", ["седан"]),
        ("minivan", ["минивэн", "minivan", "вэн"]),
        ("wagon", ["универсал", "wagon"]),
        ("liftback", ["лифтбек", "liftback"]),
    ]
    for body_type, keywords in body_keywords:
        if any(keyword in text for keyword in keywords):
            req.body_type = body_type
            break

    country_keywords = {
        "Korea": ["коре", "korea", "корей"],
        "China": ["кита", "china", "китай"],
        "Europe": ["европ", "europe", "немец", "герман"],
    }
    for country, keywords in country_keywords.items():
        if any(keyword in text for keyword in keywords):
            _append_unique(req.countries, country)

    excluded_country_phrases = {
        "Korea": ["без кореи", "корею не рассматриваю", "корея не рассматриваю", "не корея"],
        "China": ["без китая", "китай не рассматриваю", "китай пока не рассматриваю", "не китай"],
        "Europe": ["без европы", "европу не рассматриваю", "европа не рассматриваю", "не европа"],
    }
    for country, phrases in excluded_country_phrases.items():
        if any(phrase in text for phrase in phrases):
            _append_unique(req.excluded_countries, country)
            if country in req.countries:
                req.countries.remove(country)

    brand_keywords = {
        "Genesis": ["genesis", "дженезис", "генезис"],
        "Hyundai": ["hyundai", "хендай", "хендэ"],
        "Kia": ["kia", "киа"],
        "BMW": ["bmw", "бмв"],
        "Mercedes-Benz": ["mercedes", "мерседес"],
        "Audi": ["audi", "ауди"],
        "Porsche": ["porsche", "порше"],
        "Volvo": ["volvo", "вольво"],
        "Li Auto": ["li auto", "lixiang", "лисян", "ли авто"],
        "Zeekr": ["zeekr", "зикр"],
        "Tank": ["tank", "танк"],
        "Hongqi": ["hongqi", "хончи"],
        "Avatr": ["avatr", "аватр"],
    }
    for brand, keywords in brand_keywords.items():
        if any(keyword in text for keyword in keywords):
            _append_unique(req.preferred_brands, brand)

    priority_keywords = {
        "comfort": ["комфорт", "удоб", "мягк", "тих"],
        "liquidity": ["ликвид", "продать", "перепродаж"],
        "reliability": ["надеж", "надёж", "без проблем"],
        "status": ["статус", "выглядел дорого", "представитель"],
        "dynamics": ["динамик", "быстр", "мощн"],
        "family": ["семейн", "дет", "большой", "простор", "три ряда", "7 мест"],
        "low_risk": ["без лишних рисков", "без рисков", "минимум рисков", "низкий риск"],
        "equipment": ["богат", "комплектац", "оснащ", "много опций"],
    }
    for priority, keywords in priority_keywords.items():
        if any(keyword in text for keyword in keywords):
            _append_unique(req.priorities, priority)

    if "свеж" in text and req.min_year is None:
        _append_unique(req.missing_info, "Уточнить минимальный год выпуска: клиент просит свежий автомобиль.")

    if req.body_type is None and any(word in text for word in ["семейн", "большой", "простор"]):
        _append_unique(req.missing_info, "Уточнить предпочтительный кузов: SUV, minivan или wagon.")

    if req.budget_rub is None:
        _append_unique(req.missing_info, "Уточнить бюджет клиента.")

    if raw_response.startswith("LLM_ERROR"):
        _append_unique(req.missing_info, raw_response)

    req.client_profile = "Запрос разобран локальным fallback-парсером." if client_request else None
    return req


def _looks_empty(requirements: ClientRequirements) -> bool:
    return (
        requirements.budget_rub is None
        and requirements.body_type is None
        and not requirements.countries
        and not requirements.excluded_countries
        and not requirements.preferred_brands
        and not requirements.excluded_brands
        and not requirements.priorities
        and requirements.max_mileage_km is None
        and requirements.min_year is None
    )


def parse_requirements_json(raw_response: str, client_request: str = "") -> ClientRequirements:
    try:
        payload = json.loads(raw_response)
        requirements = ClientRequirements.model_validate(payload)
        if client_request and _looks_empty(requirements):
            return _heuristic_extract(client_request, raw_response)
        return requirements
    except (json.JSONDecodeError, TypeError, ValidationError):
        pass

    start = raw_response.find("{")
    end = raw_response.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            payload = json.loads(raw_response[start : end + 1])
            requirements = ClientRequirements.model_validate(payload)
            if client_request and _looks_empty(requirements):
                return _heuristic_extract(client_request, raw_response)
            return requirements
        except (json.JSONDecodeError, TypeError, ValidationError):
            pass

    if client_request:
        return _heuristic_extract(client_request, raw_response)

    return ClientRequirements(
        missing_info=[
            "Не удалось надежно извлечь требования из ответа LLM.",
            "Уточните бюджет, тип кузова, страну, год и пробег.",
        ]
    )


def extract_requirements(client_request: str, model: str | None = None) -> ClientRequirements:
    prompt = build_extraction_prompt(client_request)
    raw_response = call_llm(prompt, model=model, temperature=0.1)
    return parse_requirements_json(raw_response, client_request=client_request)
