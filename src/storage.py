from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, TextIO

import pandas as pd

from src.config import settings
from src.schemas import ClientRequirements


REQUIRED_COLUMNS = [
    "brand",
    "model",
    "country",
    "body_type",
    "year",
    "mileage_km",
    "price_rub",
    "total_price_rub",
    "engine",
    "drivetrain",
    "pros",
    "cons",
    "liquidity",
    "comfort",
    "reliability",
    "status",
    "equipment",
    "manager_notes",
]


def load_cars_csv(source: str | Path | BinaryIO | TextIO) -> pd.DataFrame:
    df = pd.read_csv(source)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"В CSV не хватает колонок: {', '.join(missing)}")
    return df[REQUIRED_COLUMNS].copy()


def save_lead(client_request: str, requirements: ClientRequirements, top_cars: pd.DataFrame) -> None:
    output_path = Path(settings.leads_log_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "client_request": client_request,
        "budget_rub": requirements.budget_rub,
        "body_type": requirements.body_type,
        "countries": json.dumps(requirements.countries, ensure_ascii=False),
        "priorities": json.dumps(requirements.priorities, ensure_ascii=False),
        "top_cars": json.dumps(
            [
                {
                    "brand": item.get("brand"),
                    "model": item.get("model"),
                    "total_price_rub": item.get("total_price_rub"),
                    "score": item.get("score"),
                }
                for item in top_cars.to_dict(orient="records")
            ],
            ensure_ascii=False,
        ),
    }

    file_exists = output_path.exists()
    with output_path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
