"""Experience analyzer package."""

from .comparer import compare_certificates_with_cv
from .models import ComparisonResult, ExperienceRecord
from .report import build_table
from .text_parser import parse_experiences_from_text

try:  # pragma: no cover - optional dependency might be missing during tests
    from .pdf_extractor import extract_text_from_pdf
except ImportError:  # pragma: no cover
    def _missing_pdf_dependency(*_args, **_kwargs):
        raise ImportError("PyMuPDF (fitz) is required for PDF extraction. Install it with `pip install pymupdf`.")

    extract_text_from_pdf = _missing_pdf_dependency  # type: ignore

__all__ = [
    "ComparisonResult",
    "ExperienceRecord",
    "compare_certificates_with_cv",
    "parse_experiences_from_text",
    "build_table",
    "extract_text_from_pdf",
]
