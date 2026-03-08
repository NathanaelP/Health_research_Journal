"""
Extract text from PDF files using PyMuPDF (fitz).
"""
import re

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def extract_text_from_pdf(file_path: str) -> tuple[str, str]:
    """
    Returns (title, body_text).
    Title is derived from PDF metadata or filename.
    """
    if not PDF_AVAILABLE:
        raise RuntimeError(
            "PyMuPDF not installed. Run: pip install pymupdf"
        )

    doc = fitz.open(file_path)

    # Try to get title from metadata
    meta = doc.metadata or {}
    title = meta.get("title", "").strip()
    if not title:
        from pathlib import Path
        title = Path(file_path).stem.replace("_", " ").replace("-", " ")

    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())

    doc.close()

    text = "\n\n".join(pages_text)
    text = _clean_whitespace(text)
    return title, text


def _clean_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
