"""Logic to match certificate experiences against CV entries."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from typing import Iterable, List, Optional

from .models import ComparisonResult, ExperienceRecord


@dataclass
class MatchScore:
    certificate: ExperienceRecord
    cv_entry: ExperienceRecord
    score: float
    start_date_match: bool


def _normalize_name(name: Optional[str]) -> str:
    if not name:
        return ""
    cleaned = name.lower()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for src, dest in replacements.items():
        cleaned = cleaned.replace(src, dest)
    return "".join(ch for ch in cleaned if ch.isalnum() or ch.isspace()).strip()


def _employer_similarity(a: Optional[str], b: Optional[str]) -> float:
    a_norm = _normalize_name(a)
    b_norm = _normalize_name(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def _date_difference(a: Optional[date], b: Optional[date]) -> Optional[int]:
    if a is None or b is None:
        return None
    return abs((a - b).days)


def _score_pair(certificate: ExperienceRecord, cv_entry: ExperienceRecord) -> MatchScore:
    similarity = _employer_similarity(certificate.employer, cv_entry.employer)
    start_diff = _date_difference(certificate.start_date, cv_entry.start_date)
    start_match = start_diff is not None and start_diff <= 7
    date_score = 1.0 if start_match else 1.0 / (1 + (start_diff or 60) / 30)
    combined_score = 0.7 * similarity + 0.3 * date_score
    return MatchScore(
        certificate=certificate,
        cv_entry=cv_entry,
        score=combined_score,
        start_date_match=start_match,
    )


def compare_certificates_with_cv(
    certificates: Iterable[ExperienceRecord],
    cv_entries: Iterable[ExperienceRecord],
) -> List[ComparisonResult]:
    cv_list = list(cv_entries)
    comparisons: List[ComparisonResult] = []
    used_cv_indices: set[int] = set()

    for certificate in certificates:
        best_score: Optional[MatchScore] = None
        for idx, cv_entry in enumerate(cv_list):
            score = _score_pair(certificate, cv_entry)
            if best_score is None or score.score > best_score.score:
                best_score = score
                best_idx = idx
        if best_score and best_score.score > 0.3:
            used_cv_indices.add(best_idx)
            comparisons.append(
                ComparisonResult(
                    certificate=certificate,
                    cv_entry=cv_list[best_idx],
                    start_date_match=best_score.start_date_match,
                    details=(
                        "Coincidencia por empleador y fecha"
                        if best_score.start_date_match
                        else "Coincidencia parcial"
                    ),
                )
            )
        else:
            comparisons.append(
                ComparisonResult(
                    certificate=certificate,
                    cv_entry=None,
                    start_date_match=False,
                    details="No se encontró coincidencia en la hoja de vida",
                )
            )

    # Add unmatched CV entries as informational rows
    for idx, cv_entry in enumerate(cv_list):
        if idx not in used_cv_indices:
            comparisons.append(
                ComparisonResult(
                    certificate=ExperienceRecord(
                        source="Hoja de vida",
                        employer=cv_entry.employer,
                        start_date=cv_entry.start_date,
                        end_date=cv_entry.end_date,
                    ),
                    cv_entry=cv_entry,
                    start_date_match=True,
                    details="Registro presente solo en la hoja de vida",
                )
            )
    return comparisons
