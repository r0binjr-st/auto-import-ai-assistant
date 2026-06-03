from __future__ import annotations

import logging

import httpx

try:
    from groq import Groq
except ImportError:  # pragma: no cover - only happens before dependencies are installed
    Groq = None

from src.config import settings


logger = logging.getLogger(__name__)


def call_llm(prompt: str, model: str | None = None, temperature: float = 0.2) -> str:
    selected_model = model or settings.groq_model_main
    if Groq is None:
        return "LLM_ERROR: groq SDK is not installed. Run pip install -r requirements.txt."

    if not settings.groq_api_key:
        return (
            "LLM_ERROR: GROQ_API_KEY is not set. Create .env from .env.example "
            "and add a Groq API key."
    )

    try:
        http_client = httpx.Client(trust_env=False, timeout=30.0)
        client = Groq(api_key=settings.groq_api_key, http_client=http_client)
        response = client.chat.completions.create(
            model=selected_model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise business assistant. Follow the user's output format exactly.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception as exc:  # pragma: no cover - depends on external API
        logger.exception("Groq call failed")
        return f"LLM_ERROR: {exc}"
