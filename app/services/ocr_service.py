"""
Extract text from image files using Tesseract OCR via pytesseract.
"""
import re
from pathlib import Path

try:
    import pytesseract
    from PIL import Image, ImageFilter, ImageEnhance
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_text_from_image(file_path: str) -> str:
    """
    Returns extracted text from an image file.
    Applies basic preprocessing to improve OCR accuracy.
    """
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "pytesseract / Pillow not installed. "
            "Run: pip install pytesseract Pillow"
        )

    img = Image.open(file_path)

    # Convert to grayscale for better OCR
    img = img.convert("L")

    # Mild sharpening
    img = img.filter(ImageFilter.SHARPEN)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    text = pytesseract.image_to_string(img, lang="eng")
    text = _clean_whitespace(text)
    return text


def _clean_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
