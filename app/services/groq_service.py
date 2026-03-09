"""
Groq API client for structured health content summarization.
Free tier at https://console.groq.com — no billing required.
Implements the same summarize(text) -> SummaryResult interface as gemini_service.py.
"""
import requests

from app.config import settings
from app.services.gemini_service import SummaryResult, PROMPT_TEMPLATE, _parse_response


def summarize(text: str) -> SummaryResult:
    """
    Send extracted text to Groq and return a structured SummaryResult.
    Raises on API error or missing key.
    """
    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "and add it to your .env file."
        )

    trimmed = text[: settings.groq_max_chars]
    prompt = PROMPT_TEMPLATE.format(text=trimmed)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": settings.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()
    parsed = _parse_response(raw)

    return SummaryResult(
        claim=parsed.get("claim", ""),
        bullets=parsed.get("bullets", []),
        detailed=parsed.get("detailed", ""),
        eli5=parsed.get("eli5", ""),
        limitations=parsed.get("limitations", ""),
        model_used=settings.groq_model,
    )
