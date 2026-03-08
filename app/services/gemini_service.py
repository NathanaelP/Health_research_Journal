"""
Gemini API client for structured health content summarization.
Designed so the AI backend can be swapped by replacing this module.
"""
import json
import re
from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class SummaryResult:
    claim: str
    bullets: list[str]
    detailed: str
    eli5: str
    limitations: str
    model_used: str


PROMPT_TEMPLATE = """\
You are a health research assistant helping a non-expert reader understand health and medical content.

Analyze the following text and respond ONLY with valid JSON in this exact format — no markdown, no code fences, no extra text:

{{
  "claim": "One sentence describing the main topic or claim of the content",
  "bullets": ["key point 1", "key point 2", "key point 3"],
  "detailed": "3-5 paragraph plain-language explanation covering what the content says, what the mechanism is, and what the evidence shows",
  "eli5": "A 2-3 sentence explanation simple enough for someone with no science background",
  "limitations": "Honest caveats — study limitations, missing context, things that are unknown or uncertain, or reasons to be cautious"
}}

Text to analyze:
---
{text}
---
"""


def summarize(text: str) -> SummaryResult:
    """
    Send extracted text to Gemini and return a structured SummaryResult.
    Raises on API error.
    """
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to your .env file."
        )

    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "google-generativeai not installed. Run: pip install google-generativeai"
        )

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    # Trim text to avoid exceeding token limits
    trimmed = text[: settings.max_text_chars]
    prompt = PROMPT_TEMPLATE.format(text=trimmed)

    response = model.generate_content(prompt)
    raw = response.text.strip()

    parsed = _parse_response(raw)
    return SummaryResult(
        claim=parsed.get("claim", ""),
        bullets=parsed.get("bullets", []),
        detailed=parsed.get("detailed", ""),
        eli5=parsed.get("eli5", ""),
        limitations=parsed.get("limitations", ""),
        model_used=settings.gemini_model,
    )


def _parse_response(raw: str) -> dict:
    """Try to parse JSON from Gemini response, with fallback cleanup."""
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract the first JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse Gemini response as JSON: {raw[:200]}")
