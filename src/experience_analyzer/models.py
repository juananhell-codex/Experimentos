"""Data models for the experience analyzer."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


def _compute_effective_end(
    start_date: Optional[date],
    end_date: Optional[date],
    issue_date: Optional[date],
) -> Optional[date]:
    """Determine the final date to count experience."""

    if start_date is None:
        return None

    candidates = [d for d in (end_date, issue_date) if d is not None]
    if not candidates:
        return None
    return min(candidates)


def _compute_days(start: Optional[date], end: Optional[date]) -> Optional[int]:
    if start is None or end is None:
        return None
    if end < start:
        return 0
    return (end - start).days + 1


@dataclass
class ExperienceRecord:
    """Represents a single experience entry extracted from a document."""

    source: str
    employer: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    issue_date: Optional[date] = None
    effective_end_date: Optional[date] = field(init=False)
    experience_days: Optional[int] = field(init=False)

    def __post_init__(self) -> None:
        self.effective_end_date = _compute_effective_end(
            self.start_date, self.end_date, self.issue_date
        )
        self.experience_days = _compute_days(self.start_date, self.effective_end_date)


@dataclass
class ComparisonResult:
    """Represents the comparison between a certificate and a CV entry."""

    certificate: ExperienceRecord
    cv_entry: Optional[ExperienceRecord]
    start_date_match: bool
    details: str
