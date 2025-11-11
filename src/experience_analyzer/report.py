"""Generate human-readable reports from comparison results."""
from __future__ import annotations

from datetime import date
from typing import Iterable, List

from .models import ComparisonResult


def _format_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def _format_days(days: int | None) -> str:
    return "" if days is None else str(days)


def _compute_widths(rows: List[List[str]]) -> List[int]:
    return [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]


def _format_row(row: List[str], widths: List[int]) -> str:
    cells = [f"{cell:<{widths[idx]}}" for idx, cell in enumerate(row)]
    return "| " + " | ".join(cells) + " |"


def build_table(comparisons: Iterable[ComparisonResult]) -> str:
    rows: List[List[str]] = []
    total_days = 0
    for comparison in comparisons:
        cert = comparison.certificate
        cv = comparison.cv_entry
        days = cert.experience_days or 0
        total_days += days
        rows.append(
            [
                cert.source,
                cert.employer or "",
                _format_date(cert.start_date),
                _format_date(cert.end_date),
                _format_date(cert.issue_date),
                _format_date(cert.effective_end_date),
                _format_days(cert.experience_days),
                "Sí" if comparison.start_date_match and cv else "No",
                cv.employer if cv else "",
                _format_date(cv.start_date if cv else None),
                _format_date(cv.end_date if cv else None),
                comparison.details,
            ]
        )
    rows.append(["", "", "", "", "", "Total", str(total_days), "", "", "", "", ""])

    headers = [
        "Fuente",
        "Entidad",
        "Ingreso (certificado)",
        "Retiro (certificado)",
        "Fecha expedición",
        "Fin contabilizado",
        "Días experiencia",
        "Coincide con HV",
        "Entidad (HV)",
        "Ingreso (HV)",
        "Retiro (HV)",
        "Detalle",
    ]

    table_data = [headers] + rows
    widths = _compute_widths(table_data)
    header_line = _format_row(headers, widths)
    separator = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    body_lines = [_format_row(row, widths) for row in rows]
    return "\n".join([header_line, separator, *body_lines])
