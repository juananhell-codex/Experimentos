from datetime import date

from experience_analyzer.comparer import compare_certificates_with_cv
from experience_analyzer.models import ExperienceRecord


def _record(source: str, employer: str, start: date, end: date) -> ExperienceRecord:
    return ExperienceRecord(
        source=source,
        employer=employer,
        start_date=start,
        end_date=end,
        issue_date=end,
    )


def test_compare_matches_by_employer_and_start_date():
    certificate = _record("Certificado: 1.pdf", "Empresa ABC", date(2020, 1, 1), date(2020, 12, 31))
    cv_entry = _record("Hoja de vida: hv.pdf", "Empresa ABC", date(2020, 1, 1), date(2020, 12, 31))

    comparisons = compare_certificates_with_cv([certificate], [cv_entry])
    assert len(comparisons) >= 1
    match = comparisons[0]
    assert match.cv_entry is not None
    assert match.start_date_match is True
    assert "Coincidencia" in match.details
