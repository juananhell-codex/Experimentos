"""Parsing utilities for extracting structured data from raw text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional, Sequence

from .models import ExperienceRecord

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

DATE_PATTERN = re.compile(
    r"""
    (?P<date>
        \d{1,2}[/-]\d{1,2}[/-]\d{2,4}
        |
        \d{4}-\d{2}-\d{2}
        |
        \d{1,2}\s+(?:de\s+|d[ií]as\s+del\s+mes\s+de\s+)[a-zA-Záéíóúñ]+\s+de\s+\d{4}
        |
        [a-zA-Záéíóúñ]+\s+\d{1,2},\s*\d{4}
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

KEYWORD_GROUPS = {
    "start": ["ingreso", "inicio", "desde", "vinculación", "vinculo", "se vinculó"],
    "end": [
        "retiro",
        "terminación",
        "hasta",
        "culminación",
        "finalización",
        "finalizo",
        "finalizó",
    ],
    "issue": ["expedido", "expide", "emitido", "fecha de expedición"],
}

EMPLOYER_HINTS = [
    "empresa",
    "entidad",
    "compañía",
    "compania",
    "organización",
    "organizacion",
    "institución",
    "institucion",
    "razón social",
    "razon social",
    "dependencia",
]


def _parse_numeric_date(text: str) -> Optional[date]:
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            year = dt.year
            if year < 100:
                year += 2000 if year < 50 else 1900
            return date(year, dt.month, dt.day)
        except ValueError:
            continue
    return None


def _parse_spanish_date(text: str) -> Optional[date]:
    match = re.match(
        r"(?P<day>\d{1,2})\s+(?:de\s+|d[ií]as\s+del\s+mes\s+de\s+)(?P<month>[a-záéíóúñ]+)\s+de\s+(?P<year>\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        month_name = match.group("month").lower()
        month = MONTHS.get(month_name)
        if month:
            return date(int(match.group("year")), month, int(match.group("day")))
    match = re.match(
        r"(?P<month>[a-záéíóúñ]+)\s+(?P<day>\d{1,2}),\s*(?P<year>\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        month_name = match.group("month").lower()
        month = MONTHS.get(month_name)
        if month:
            return date(int(match.group("year")), month, int(match.group("day")))
    return None


def _parse_date(text: str) -> Optional[date]:
    cleaned = text.strip()
    return _parse_numeric_date(cleaned) or _parse_spanish_date(cleaned)


@dataclass
class ParsedSection:
    """Represents a chunk of text that might describe a single experience."""

    lines: List[str]

    def text(self) -> str:
        return "\n".join(self.lines)


def split_into_sections(text: str) -> List[ParsedSection]:
    lines = [line.strip() for line in text.splitlines()]
    sections: List[ParsedSection] = []
    buffer: List[str] = []
    for line in lines:
        if not line:
            if buffer:
                sections.append(ParsedSection(lines=buffer.copy()))
                buffer.clear()
            continue
        buffer.append(line)
    if buffer:
        sections.append(ParsedSection(lines=buffer))
    return sections


def _find_first_matching_date(
    section_text: str,
    keywords: Sequence[str],
    *,
    position: str = "before",
) -> Optional[date]:
    lowered = section_text.lower()
    matches = list(DATE_PATTERN.finditer(section_text))
    for match in matches:
        span_start = match.start()
        span_end = match.end()
        before = lowered[max(span_start - 80, 0):span_start]
        after = lowered[span_end:min(span_end + 80, len(section_text))]
        before_match = position in ("before", "any") and any(keyword in before for keyword in keywords)
        after_match = position in ("after", "any") and any(keyword in after for keyword in keywords)
        if before_match or after_match:
            parsed = _parse_date(match.group("date"))
            if parsed:
                return parsed
    return None


def _extract_issue_date(section: ParsedSection) -> Optional[date]:
    section_text = section.text()
    date_candidates = list(DATE_PATTERN.finditer(section_text))
    if not date_candidates:
        return None
    last_candidate = date_candidates[-1].group("date")
    return _parse_date(last_candidate)


def _extract_employer(section: ParsedSection) -> Optional[str]:
    for line in section.lines:
        lowered = line.lower()
        if any(hint in lowered for hint in EMPLOYER_HINTS):
            cleaned = re.sub(
                r"(?i)(empresa|entidad|compa[ñn]ía|organización|organizacion|instituci[óo]n|raz[óo]n social|dependencia|:)",
                "",
                line,
            )
            cleaned = cleaned.strip(" -:")
            if cleaned:
                return cleaned
    candidate = max((line for line in section.lines if line.strip()), key=len, default=None)
    if candidate:
        return candidate.strip()
    return None


def parse_experiences_from_text(text: str, source: str) -> List[ExperienceRecord]:
    sections = split_into_sections(text)
    experiences: List[ExperienceRecord] = []
    if not sections:
        sections = [ParsedSection(lines=[text])]

    for section in sections:
        section_text = section.text()
        start_date = _find_first_matching_date(section_text, KEYWORD_GROUPS["start"], position="before")
        end_date = _find_first_matching_date(section_text, KEYWORD_GROUPS["end"], position="before")
        issue_date = _find_first_matching_date(section_text, KEYWORD_GROUPS["issue"], position="before")
        if issue_date is None:
            issue_date = _extract_issue_date(section)
        if not any([start_date, end_date, issue_date]):
            continue
        employer = _extract_employer(section)
        experiences.append(
            ExperienceRecord(
                source=source,
                employer=employer,
                start_date=start_date,
                end_date=end_date,
                issue_date=issue_date,
            )
        )
    return experiences


def merge_overlapping_records(records: Iterable[ExperienceRecord]) -> List[ExperienceRecord]:
    """Merge records that share the same employer and overlapping dates."""

    grouped: dict[str, List[ExperienceRecord]] = {}
    for record in records:
        key = (record.employer or "").strip().lower()
        grouped.setdefault(key, []).append(record)

    merged: List[ExperienceRecord] = []
    for items in grouped.values():
        items = sorted(
            items,
            key=lambda rec: rec.start_date or date.min,
        )
        if not items:
            continue
        current = items[0]
        for next_item in items[1:]:
            if (
                current.start_date
                and next_item.start_date
                and current.effective_end_date
                and next_item.start_date <= current.effective_end_date
            ):
                if (
                    next_item.effective_end_date
                    and (
                        current.effective_end_date is None
                        or next_item.effective_end_date > current.effective_end_date
                    )
                ):
                    current.end_date = next_item.end_date or current.end_date
                    current.issue_date = next_item.issue_date or current.issue_date
                    current.__post_init__()
            else:
                merged.append(current)
                current = next_item
        merged.append(current)
    return merged
