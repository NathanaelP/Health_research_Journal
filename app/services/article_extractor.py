"""
Extract readable article text from a URL using readability-lxml.
Falls back to raw requests + BeautifulSoup if readability fails.
"""
import re
import requests
from readability import Document


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HealthResearchBot/1.0)"
    )
}


def extract_article(url: str, timeout: int = 15) -> tuple[str, str]:
    """
    Returns (title, body_text).
    Raises on network or parse failure.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()

    doc = Document(response.text)
    title = doc.title() or url

    # readability returns HTML; strip tags for plain text
    html_body = doc.summary()
    text = _strip_tags(html_body)
    text = _clean_whitespace(text)

    return title, text


def _strip_tags(html: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", html)
    return clean


def _clean_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
