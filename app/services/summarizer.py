"""
Orchestrates the full intake pipeline:
  receive input → extract text → call Gemini → save to DB
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Item, Summary
from app.config import settings


async def process_item(
    db: Session,
    user_id: int,
    source_type: str,
    source_url: Optional[str] = None,
    file_path: Optional[str] = None,
    raw_text: Optional[str] = None,
    original_filename: Optional[str] = None,
    title: Optional[str] = None,
) -> Item:
    """
    Full pipeline: extract text, summarize, persist, return Item.
    If Gemini fails, the item is still saved with extracted text so
    nothing is lost — summary will just be missing.
    """
    extracted_text = ""
    derived_title = title or "Untitled"

    # --- Step 1: Extract text ---
    try:
        if source_type == "link" and source_url:
            from app.services.article_extractor import extract_article
            derived_title, extracted_text = extract_article(source_url)

        elif source_type == "screenshot" and file_path:
            from app.services.ocr_service import extract_text_from_image
            extracted_text = extract_text_from_image(file_path)
            derived_title = original_filename or Path(file_path).name

        elif source_type == "pdf" and file_path:
            from app.services.pdf_service import extract_text_from_pdf
            derived_title, extracted_text = extract_text_from_pdf(file_path)

        elif source_type == "text" and raw_text:
            extracted_text = raw_text

    except Exception as e:
        extracted_text = f"[Extraction error: {e}]"

    # Use provided title if extraction didn't produce one
    if title:
        derived_title = title

    extracted_text = _clean(extracted_text)

    # --- Step 2: Save item ---
    item = Item(
        title=derived_title[:500],
        source_type=source_type,
        source_url=source_url,
        original_file_path=file_path,
        raw_text=raw_text or "",
        extracted_text=extracted_text,
        created_by=user_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # --- Step 3: Summarize ---
    await _run_summary(db, item, extracted_text)

    return item


async def regenerate_summary(db: Session, item: Item) -> None:
    """Re-run Gemini summarization on an existing item."""
    await _run_summary(db, item, item.extracted_text)


async def _run_summary(db: Session, item: Item, text: str) -> None:
    if not text or text.startswith("[Extraction error"):
        return

    try:
        from app.services.gemini_service import summarize
        result = summarize(text)

        if item.summary:
            summary = item.summary
        else:
            summary = Summary(item_id=item.id)
            db.add(summary)

        summary.claim = result.claim
        summary.bullet_summary = json.dumps(result.bullets)
        summary.detailed_explanation = result.detailed
        summary.eli5_explanation = result.eli5
        summary.limitations = result.limitations
        summary.model_used = result.model_used
        summary.created_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        # Don't lose the item — just log and continue
        print(f"[WARN] Gemini summarization failed for item {item.id}: {e}")


def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
