"""Utilities for extracting text from PDF files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import logging

try:
    import fitz  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency missing handled by runtime error
    raise ImportError(
        "PyMuPDF (fitz) is required to extract text from PDF files. "
        "Please install it with `pip install pymupdf`."
    ) from exc

try:
    import pytesseract  # type: ignore
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency
    pytesseract = None  # type: ignore
    Image = None  # type: ignore

import io
import shutil

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of extracting text from a PDF."""

    text: str
    method: str


def _page_text(page: "fitz.Page") -> str:
    return page.get_text("text") or ""


def _needs_ocr(text: str) -> bool:
    cleaned = text.strip()
    # Heuristic: if text is mostly whitespace or very short we assume OCR is required
    return len(cleaned) < 30


def _perform_ocr(pages: List["fitz.Page"]) -> str:
    if pytesseract is None or Image is None:
        logger.warning(
            "pytesseract/Pillow not installed; OCR step skipped. Text extraction may be incomplete."
        )
        return ""

    if shutil.which("tesseract") is None:
        logger.warning(
            "Tesseract OCR binary is not available in PATH; OCR step skipped. Text extraction may be incomplete."
        )
        return ""

    ocr_text: List[str] = []
    for index, page in enumerate(pages):
        pix = page.get_pixmap(dpi=300)
        image_bytes = pix.tobytes(output="png")
        with Image.open(io.BytesIO(image_bytes)) as image:
            text = pytesseract.image_to_string(image, lang="spa+eng")
            logger.debug("OCR extracted %d characters from page %d", len(text), index)
            ocr_text.append(text)
    return "\n".join(ocr_text)


def extract_text_from_pdf(path: Path, *, enable_ocr: bool = True) -> ExtractionResult:
    """Extract text from *path*.

    The function first attempts to use the text layer available in the PDF. When the
    result appears to be empty it optionally falls back to OCR using pytesseract.
    """

    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    try:
        text_segments = [_page_text(page) for page in doc]
        joined_text = "\n".join(text_segments)
        method = "text"

        if enable_ocr and _needs_ocr(joined_text):
            logger.info("Text layer is scarce; attempting OCR for %s", pdf_path.name)
            ocr_text = _perform_ocr(list(doc))
            if ocr_text.strip():
                joined_text = ocr_text
                method = "ocr"
        return ExtractionResult(text=joined_text, method=method)
    finally:
        doc.close()
