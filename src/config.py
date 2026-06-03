from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None = os.getenv("GROQ_API_KEY") or None
    groq_model_main: str = os.getenv("GROQ_MODEL_MAIN", "llama-3.3-70b-versatile")
    groq_model_fast: str = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
    outputs_dir: str = "outputs"
    leads_log_path: str = "outputs/leads_log.csv"


settings = Settings()
