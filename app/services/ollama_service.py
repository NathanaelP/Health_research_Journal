"""
Ollama local LLM client for structured health content summarization.
Implements the same summarize(text) -> SummaryResult interface as gemini_service.py.
"""
import json
import re

import requests

from app.config import settings
from app.services.gemini_service import SummaryResult, PROMPT_TEMPLATE, _parse_response


def summarize(text: str) -> SummaryResult:
    """
    Send extracted text to a local Ollama instance and return a structured SummaryResult.
    Raises on connection error or bad response.
    """
    trimmed = text[: settings.max_text_chars]
    prompt = PROMPT_TEMPLATE.format(text=trimmed)

    try:
        response = requests.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=600,  # local models on Pi 3 can be slow; runs as background task
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not connect to Ollama at {settings.ollama_url}. "
            "Is Ollama running? Try: ollama serve"
        )

    raw = response.json().get("response", "").strip()
    parsed = _parse_response(raw)

    return SummaryResult(
        claim=parsed.get("claim", ""),
        bullets=parsed.get("bullets", []),
        detailed=parsed.get("detailed", ""),
        eli5=parsed.get("eli5", ""),
        limitations=parsed.get("limitations", ""),
        model_used=settings.ollama_model,
    )
