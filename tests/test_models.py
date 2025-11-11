from datetime import date

from experience_analyzer.models import ExperienceRecord


def test_effective_end_uses_earliest_of_end_and_issue():
    record = ExperienceRecord(
        source="Certificado",
        employer="Empresa",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
        issue_date=date(2020, 6, 30),
    )
    assert record.effective_end_date == date(2020, 6, 30)
    assert record.experience_days == 182


def test_effective_end_returns_none_without_dates():
    record = ExperienceRecord(
        source="Certificado",
        employer="Empresa",
        start_date=None,
        end_date=None,
        issue_date=None,
    )
    assert record.effective_end_date is None
    assert record.experience_days is None
